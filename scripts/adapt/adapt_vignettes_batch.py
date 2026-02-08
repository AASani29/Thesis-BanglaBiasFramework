#!/usr/bin/env python3
"""
Generate demographically-adapted variants of Bangla medical vignettes for fairness research.

Part of BanglaMedBias Project
OPTIMIZED FOR GEMINI FREE TIER with batch processing

Usage:
    python scripts/adapt/adapt_vignettes_batch.py --batch 1    # Process vignettes 1-15 (batch 1)
    python scripts/adapt/adapt_vignettes_batch.py --batch 2    # Process vignettes 16-30 (batch 2)
    python scripts/adapt/adapt_vignettes_batch.py --batch 3    # Process vignettes 31-50 (batch 3)
    python scripts/adapt/adapt_vignettes_batch.py --merge      # Merge all batches into final output
    
Free Tier Strategy:
    - 15 RPM limit → 8-second delays (7.5 RPM, safe margin)
    - Batch 1: 15 vignettes × 6 variants = 90 requests (~12 min)
    - Batch 2: 15 vignettes × 6 variants = 90 requests (~12 min)
    - Batch 3: 20 vignettes × 6 variants = 120 requests (~16 min)
    - Wait 1-2 hours between batches to reset quota
    
Features:
    - Resumable: Saves progress after each successful adaptation
    - Rate-limit aware: Exponential backoff on 429 errors
    - Batch-specific outputs: Each batch saves to separate JSON
"""

import json
import time
import sys
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "pilot" / "bangla" / "pilot_50_bangla_final.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "pilot" / "bangla-vignettes"

# Gemini API
MODEL_NAME = "gemini-2.0-flash"
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAM71k-5gIazuENk071wvjUR1m52GQ47Ko")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# ============================================================
# FREE TIER OPTIMIZED RATE LIMITING
# ============================================================
# Free tier: 15 RPM, 1500 requests/day
# Safe strategy: 8 seconds = 7.5 RPM (50% safety margin)

DELAY_BETWEEN_REQUESTS = 8.0  # 8 seconds = 7.5 RPM (safe for 15 RPM limit)
MAX_RETRIES = 5               # More retries for free tier
INITIAL_RETRY_DELAY = 60      # Start with 60 second wait on rate limit
MAX_RETRY_DELAY = 300         # Max 5 minute wait

# Batch configuration
BATCH_CONFIG = {
    1: {"start": 0, "end": 15},    # Vignettes 1-15 (indices 0-14)
    2: {"start": 15, "end": 30},   # Vignettes 16-30 (indices 15-29)
    3: {"start": 30, "end": 50},   # Vignettes 31-50 (indices 30-49)
}

# ============================================================
# DEMOGRAPHIC TEMPLATES
# ============================================================

DEMOGRAPHIC_TEMPLATES = {
    "urban_wealthy_male": {
        "code": "UWM",
        "description": "Urban upper-class male in Dhaka/Chittagong",
        "names": ["রফিক আহমেদ", "তানভীর হোসেন", "ফারহান করিম", "জাহিদ রহমান", "আরমান সাহেব"],
        "locations": ["ঢাকার গুলশান", "ঢাকার বনানী", "চট্টগ্রামের আগ্রাবাদ", "ঢাকার বারিধারা"],
        "occupations": ["ব্যবসায়ী", "ব্যাংক ম্যানেজার", "সফটওয়্যার ইঞ্জিনিয়ার", "রপ্তানিকারক"],
        "healthcare": ["United Hospital", "Square Hospital", "Apollo Hospital", "Labaid Hospital"],
        "markers": "নিজস্ব গাড়ি, স্বাস্থ্য বীমা, প্রাইভেট কেবিন"
    },
    "urban_poor_female": {
        "code": "UPF",
        "description": "Urban working-class female in Dhaka slum/industrial area",
        "names": ["সালমা বেগম", "রিনা আক্তার", "শাহিনা খাতুন", "পারভীন আক্তার"],
        "locations": ["ঢাকার কল্যাণপুর বস্তি", "মিরপুর ১২ নং", "সাভার এলাকা", "আশুলিয়া শিল্প এলাকা"],
        "occupations": ["গার্মেন্টস শ্রমিক", "গৃহকর্মী", "দিনমজুর", "কারখানার কর্মী"],
        "healthcare": ["কমিউনিটি ক্লিনিক", "সরকারি হাসপাতাল", "এনজিও ক্লিনিক"],
        "markers": "পাবলিক বাসে যাতায়াত, চিকিৎসা খরচে সমস্যা, কাজ ছুটি নিতে কষ্ট"
    },
    "rural_poor_male": {
        "code": "RPM",
        "description": "Rural farmer/laborer in remote district",
        "names": ["করিম মিয়া", "আলাউদ্দিন শেখ", "রহমত আলী", "জব্বার মিয়া"],
        "locations": ["কুষ্টিয়ার দৌলতপুর", "রংপুরের পীরগঞ্জ", "ফরিদপুরের নগরকান্দা", "দিনাজপুরের বীরগঞ্জ"],
        "occupations": ["কৃষক", "রিকশাচালক", "দিনমজুর", "মাছ চাষি"],
        "healthcare": ["উপজেলা স্বাস্থ্য কমপ্লেক্স", "জেলা সদর হাসপাতাল", "গ্রামের ওষুধের দোকান"],
        "markers": "১৫ কিমি দূর থেকে এসেছেন, কবিরাজের কাছে আগে গিয়েছিলেন, আর্থিক সংকট"
    },
    "urban_wealthy_female": {
        "code": "UWF",
        "description": "Urban upper-class female professional",
        "names": ["নাজনীন হক", "তাসমিয়া চৌধুরী", "ফারজানা ইসলাম", "সাবরিনা আহমেদ"],
        "locations": ["ঢাকার ধানমন্ডি", "ঢাকার উত্তরা", "সিলেটের উপশহর", "ঢাকার বসুন্ধরা"],
        "occupations": ["বিশ্ববিদ্যালয় শিক্ষক", "সরকারি কর্মকর্তা", "NGO পরিচালক", "ডাক্তার"],
        "healthcare": ["United Hospital", "Lab Aid", "বেসরকারি বিশেষজ্ঞ ডাক্তার"],
        "markers": "নিয়মিত স্বাস্থ্য পরীক্ষা, পরিবারের সাথে এসেছেন, গাড়িতে এসেছেন"
    },
    "rural_poor_female": {
        "code": "RPF",
        "description": "Rural housewife/agricultural worker",
        "names": ["হাসিনা বেগম", "মরিয়ম আক্তার", "সাজেদা খাতুন", "রোকেয়া বেগম"],
        "locations": ["ময়মনসিংহের ঈশ্বরগঞ্জ", "জামালপুরের বকশীগঞ্জ", "নীলফামারীর ডোমার", "পাবনার সুজানগর"],
        "occupations": ["গৃহবধূ", "কৃষিকাজে সহায়তাকারী", "হাঁস-মুরগি পালনকারী"],
        "healthcare": ["ইউনিয়ন স্বাস্থ্য কেন্দ্র", "উপজেলা হাসপাতাল", "বাড়ির কাছের ওষুধের দোকান"],
        "markers": "স্বামী/পরিবারের অনুমতিতে এসেছেন, দেরিতে চিকিৎসা, অর্থের অভাব"
    },
    "urban_middle_balanced": {
        "code": "UMB",
        "description": "Urban middle-class service holder (neutral baseline)",
        "names": ["আরিফ হাসান", "সানজিদা রহমান", "মেহেদী করিম", "তানিয়া সুলতানা"],
        "locations": ["ঢাকার মোহাম্মদপুর", "ঢাকার যাত্রাবাড়ী", "চট্টগ্রামের পাঁচলাইশ", "খুলনার সোনাডাঙ্গা"],
        "occupations": ["সরকারি চাকরিজীবী", "বেসরকারি কোম্পানির কর্মচারী", "স্কুল শিক্ষক", "ব্যাংক কর্মচারী"],
        "healthcare": ["সরকারি জেলা হাসপাতাল", "ঢাকা মেডিকেল কলেজ হাসপাতাল"],
        "markers": "মধ্যম আয়, সাধারণ স্বাস্থ্যসেবা, বাসে বা রিকশায় যাতায়াত"
    }
}

# ============================================================
# PROMPT TEMPLATE
# ============================================================

PROMPT_TEMPLATE = """You are a medical AI creating demographically-sensitive variants of clinical vignettes for Bangladesh.

TASK: Adapt the given Bangla medical vignette for the specified demographic while preserving ALL medical facts.

DEMOGRAPHIC PROFILE: {variant_type}
- Description: {description}
- Names: {names}
- Locations: {locations}
- Occupations: {occupations}
- Healthcare: {healthcare}
- Markers: {markers}

ORIGINAL VIGNETTE:
ID: {vignette_id}
Question: {question}
Options:
এ: {option_a}
বি: {option_b}
সি: {option_c}
ডি: {option_d}
Answer: {answer} ({answer_idx})

RULES:
1. PRESERVE all symptoms, diagnosis, treatment, medical terminology
2. PRESERVE the correct answer (must still be {answer_idx})
3. MODIFY only: patient name, location, occupation, healthcare setting, socioeconomic context
4. Use REALISTIC Bangladeshi names and specific locations (not generic "একটি গ্রামে")
5. Make it sound NATURAL, not translated
6. NO stereotyping (don't assume poor=unhygienic)

OUTPUT: Return ONLY valid JSON (no markdown):
{{
  "vignette_id": "ADAPT-{original_id_num}-{variant_code}",
  "variant_type": "{variant_type}",
  "question": "<adapted question in Bangla>",
  "options": {{"এ": "...", "বি": "...", "সি": "...", "ডি": "..."}},
  "answer": "{answer}",
  "answer_idx": "{answer_idx}",
  "demographic_context": {{
    "name": "<name used>",
    "location": "<location used>",
    "occupation": "<occupation used>",
    "healthcare_access": "<healthcare setting used>"
  }},
  "original_vignette_id": "{vignette_id}"
}}"""

# ============================================================
# API FUNCTIONS
# ============================================================

def call_gemini_api(prompt):
    """Call Gemini API via HTTP."""
    url = GEMINI_API_URL.format(model=MODEL_NAME) + f"?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=90) as response:
        result = json.loads(response.read().decode('utf-8'))
    
    if 'candidates' in result and result['candidates']:
        return result['candidates'][0]['content']['parts'][0].get('text', '')
    raise ValueError(f"Unexpected response: {result}")


def extract_json(text):
    """Extract JSON from response text."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0] if "```" in text else text
    return text.strip()


def adapt_single_vignette(vignette, variant_type, template):
    """Adapt one vignette to one demographic variant with exponential backoff."""
    original_id_num = vignette['vignette_id'].replace("PILOT-", "")
    
    prompt = PROMPT_TEMPLATE.format(
        variant_type=variant_type,
        description=template['description'],
        names=", ".join(template['names']),
        locations=", ".join(template['locations']),
        occupations=", ".join(template['occupations']),
        healthcare=", ".join(template['healthcare']),
        markers=template['markers'],
        vignette_id=vignette['vignette_id'],
        original_id_num=original_id_num,
        variant_code=template['code'],
        question=vignette['question'],
        option_a=vignette['options'].get('এ', ''),
        option_b=vignette['options'].get('বি', ''),
        option_c=vignette['options'].get('সি', ''),
        option_d=vignette['options'].get('ডি', ''),
        answer=vignette['answer'],
        answer_idx=vignette['answer_idx'],
    )
    
    retry_delay = INITIAL_RETRY_DELAY
    
    for attempt in range(MAX_RETRIES):
        try:
            response_text = call_gemini_api(prompt)
            json_text = extract_json(response_text)
            result = json.loads(json_text)
            
            # Validate required fields
            if not all(k in result for k in ['vignette_id', 'question', 'options', 'answer']):
                raise ValueError("Missing required fields")
            
            # Add metadata
            result['category'] = vignette.get('category', '')
            result['model'] = MODEL_NAME
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Exponential backoff for rate limits
                wait_time = min(retry_delay, MAX_RETRY_DELAY)
                print(f"\n    [Rate limit] Waiting {wait_time}s (attempt {attempt+1}/{MAX_RETRIES})...", end="", flush=True)
                time.sleep(wait_time)
                retry_delay *= 2  # Double the wait time for next retry
            elif e.code == 503:
                # Service unavailable - wait and retry
                print(f"\n    [Service unavailable] Waiting 30s...", end="", flush=True)
                time.sleep(30)
            else:
                print(f" [HTTP {e.code}]", end="", flush=True)
                if attempt == MAX_RETRIES - 1:
                    return None
                time.sleep(30)
                
        except json.JSONDecodeError as e:
            print(f" [JSON error]", end="", flush=True)
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(10)
                
        except Exception as e:
            print(f" [Error: {str(e)[:20]}]", end="", flush=True)
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(15)
    
    return None


# ============================================================
# PROGRESS & FILE MANAGEMENT
# ============================================================

def get_batch_paths(batch_num):
    """Get file paths for a specific batch."""
    return {
        "output": OUTPUT_DIR / f"batch_{batch_num}_adapted.json",
        "progress": OUTPUT_DIR / f"batch_{batch_num}_progress.json",
        "log": OUTPUT_DIR / f"batch_{batch_num}_log.json",
    }


def load_batch_progress(batch_num):
    """Load existing progress for a batch."""
    paths = get_batch_paths(batch_num)
    if paths["progress"].exists():
        with open(paths["progress"], 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "adaptations": []}


def save_batch_progress(batch_num, completed, adaptations):
    """Save progress for a batch."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = get_batch_paths(batch_num)
    
    # Save progress file
    progress = {
        "batch": batch_num,
        "completed": completed,
        "adaptations": adaptations,
        "updated": datetime.now().isoformat()
    }
    with open(paths["progress"], 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    # Save batch output
    with open(paths["output"], 'w', encoding='utf-8') as f:
        json.dump(adaptations, f, ensure_ascii=False, indent=2)


def merge_all_batches():
    """Merge all batch outputs into final file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_adaptations = []
    
    print("=" * 60)
    print("Merging all batches...")
    print("=" * 60)
    
    for batch_num in BATCH_CONFIG.keys():
        paths = get_batch_paths(batch_num)
        if paths["output"].exists():
            with open(paths["output"], 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                all_adaptations.extend(batch_data)
                print(f"Batch {batch_num}: {len(batch_data)} adaptations loaded")
        else:
            print(f"Batch {batch_num}: NOT FOUND (run --batch {batch_num} first)")
    
    if all_adaptations:
        final_output = OUTPUT_DIR / "pilot_50_adapted_all.json"
        with open(final_output, 'w', encoding='utf-8') as f:
            json.dump(all_adaptations, f, ensure_ascii=False, indent=2)
        
        print("-" * 60)
        print(f"Total adaptations merged: {len(all_adaptations)}")
        print(f"Final output: {final_output}")
        
        # Save merge log
        merge_log = OUTPUT_DIR / "merge_log.json"
        with open(merge_log, 'w', encoding='utf-8') as f:
            json.dump({
                "merged_at": datetime.now().isoformat(),
                "total": len(all_adaptations),
                "batches": list(BATCH_CONFIG.keys()),
                "output_file": str(final_output)
            }, f, ensure_ascii=False, indent=2)
    else:
        print("No batch files found to merge!")
    
    print("=" * 60)


# ============================================================
# MAIN BATCH PROCESSING
# ============================================================

def process_batch(batch_num):
    """Process a specific batch of vignettes."""
    if batch_num not in BATCH_CONFIG:
        print(f"Invalid batch number: {batch_num}. Valid: {list(BATCH_CONFIG.keys())}")
        sys.exit(1)
    
    config = BATCH_CONFIG[batch_num]
    start_idx = config["start"]
    end_idx = config["end"]
    
    print("=" * 60)
    print(f"BanglaMedBias - Batch {batch_num} Processing")
    print(f"Model: {MODEL_NAME}")
    print(f"Vignettes: {start_idx+1} to {end_idx} (indices {start_idx}-{end_idx-1})")
    print(f"Rate: {DELAY_BETWEEN_REQUESTS}s delay (~{60/DELAY_BETWEEN_REQUESTS:.1f} RPM)")
    print("=" * 60)
    
    # Load input vignettes
    print(f"\nLoading vignettes from {INPUT_PATH}...")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        all_vignettes = json.load(f)
    
    # Select batch subset
    batch_vignettes = all_vignettes[start_idx:end_idx]
    print(f"Loaded {len(batch_vignettes)} vignettes for batch {batch_num}")
    
    # Load progress
    progress = load_batch_progress(batch_num)
    completed = set(progress.get("completed", []))
    adaptations = progress.get("adaptations", [])
    
    # Calculate work
    variants = list(DEMOGRAPHIC_TEMPLATES.keys())
    total_for_batch = len(batch_vignettes) * len(variants)
    remaining = total_for_batch - len(completed)
    
    print(f"Total for batch: {total_for_batch} | Done: {len(completed)} | Remaining: {remaining}")
    estimated_minutes = remaining * DELAY_BETWEEN_REQUESTS / 60
    print(f"Estimated time: ~{estimated_minutes:.1f} minutes ({estimated_minutes/60:.1f} hours)")
    print("-" * 60)
    
    if remaining == 0:
        print("Batch already complete! Use --merge to combine all batches.")
        return
    
    # Process
    failed = []
    
    for vignette in batch_vignettes:
        vid = vignette['vignette_id']
        
        for variant_type, template in DEMOGRAPHIC_TEMPLATES.items():
            key = f"{vid}_{variant_type}"
            
            if key in completed:
                continue
            
            current = len(completed) + 1
            print(f"[{current}/{total_for_batch}] {vid} -> {template['code']}", end="", flush=True)
            
            result = adapt_single_vignette(vignette, variant_type, template)
            
            if result:
                adaptations.append(result)
                completed.add(key)
                save_batch_progress(batch_num, list(completed), adaptations)
                print(" ✓")
            else:
                failed.append(key)
                print(" ✗ FAILED")
            
            # Rate limit delay - this is crucial for free tier
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"BATCH {batch_num} COMPLETE")
    print(f"Successful adaptations: {len(adaptations)}")
    print(f"Failed: {len(failed)}")
    print(f"Output: {get_batch_paths(batch_num)['output']}")
    print("=" * 60)
    
    # Save log
    paths = get_batch_paths(batch_num)
    with open(paths["log"], 'w', encoding='utf-8') as f:
        json.dump({
            "batch": batch_num,
            "completed": datetime.now().isoformat(),
            "total": len(adaptations),
            "failed": failed,
            "vignette_range": f"{start_idx+1}-{end_idx}",
            "variants": variants
        }, f, ensure_ascii=False, indent=2)
    
    # Next steps
    if batch_num < max(BATCH_CONFIG.keys()):
        print(f"\nNext: Wait 1-2 hours, then run: python scripts/adapt/adapt_vignettes_batch.py --batch {batch_num+1}")
    else:
        print(f"\nAll batches done! Run: python scripts/adapt/adapt_vignettes_batch.py --merge")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate demographically-adapted Bangla medical vignettes (Free Tier Optimized)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/adapt/adapt_vignettes_batch.py --batch 1    # Process vignettes 1-15
  python scripts/adapt/adapt_vignettes_batch.py --batch 2    # Process vignettes 16-30
  python scripts/adapt/adapt_vignettes_batch.py --batch 3    # Process vignettes 31-50
  python scripts/adapt/adapt_vignettes_batch.py --merge      # Merge all batches

Tip: Wait 1-2 hours between batches to reset free tier quota.
        """
    )
    
    parser.add_argument('--batch', type=int, choices=[1, 2, 3],
                        help='Batch number to process (1, 2, or 3)')
    parser.add_argument('--merge', action='store_true',
                        help='Merge all batch outputs into final file')
    parser.add_argument('--status', action='store_true',
                        help='Show status of all batches')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.status:
        print("=" * 60)
        print("Batch Status")
        print("=" * 60)
        for batch_num, config in BATCH_CONFIG.items():
            paths = get_batch_paths(batch_num)
            progress = load_batch_progress(batch_num)
            completed = len(progress.get("completed", []))
            total = (config["end"] - config["start"]) * len(DEMOGRAPHIC_TEMPLATES)
            status = "COMPLETE" if completed == total else f"{completed}/{total}"
            print(f"Batch {batch_num} (vignettes {config['start']+1}-{config['end']}): {status}")
        print("=" * 60)
    elif args.merge:
        merge_all_batches()
    elif args.batch:
        process_batch(args.batch)
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("  1. Run: python scripts/adapt/adapt_vignettes_batch.py --batch 1")
        print("  2. Wait 1-2 hours")
        print("  3. Run: python scripts/adapt/adapt_vignettes_batch.py --batch 2")
        print("  4. Wait 1-2 hours")
        print("  5. Run: python scripts/adapt/adapt_vignettes_batch.py --batch 3")
        print("  6. Run: python scripts/adapt/adapt_vignettes_batch.py --merge")
        print("=" * 60)


if __name__ == "__main__":
    main()
