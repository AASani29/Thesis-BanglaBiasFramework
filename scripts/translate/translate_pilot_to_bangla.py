#!/usr/bin/env python3
"""
Translate 50 pilot English medical vignettes to Bangla using Gemini 2.0 Flash.

Part of BanglaMedBias Project - Pilot Phase
Step 1B: Translate 50 vignettes to Bangla

Usage:
    python scripts/translate/translate_pilot_to_bangla.py

Requirements:
    - Google AI API key (free from https://aistudio.google.com/)
    - Set GOOGLE_API_KEY in .env file or environment variable

Why Gemini over mBART/NLLB:
    - Superior Bangla language quality (Google's Bangla training data is unmatched)
    - Understands medical context — won't mistranslate clinical terminology
    - Can distinguish Bangladesh Bangla from West Bengal Bangla
    - Cost: ~$0.00-0.50 for 50 vignettes (vs. free but poor quality from NLLB)
    - For only 50 items, API quality >>> local model quality
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

import google.generativeai as genai

# ============================================================
# CONFIGURATION
# ============================================================

# Model selection - Gemini 2.0 Flash is free tier and excellent for Bangla
MODEL_NAME = "gemini-2.0-flash"

# Paths
INPUT_PATH = project_root / "data" / "pilot" / "pilot_50_from_fairmedqa.json"
OUTPUT_DIR = project_root / "data" / "pilot" / "bangla"
OUTPUT_PATH = OUTPUT_DIR / "pilot_50_bangla.json"
LOG_PATH = OUTPUT_DIR / "translation_log.json"

# Rate limiting (Gemini free tier: 15 RPM, 1500 RPD)
REQUESTS_PER_MINUTE = 14  # Stay under 15 RPM limit
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE  # ~4.3 seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

# ============================================================
# TRANSLATION PROMPT
# ============================================================

SYSTEM_PROMPT = """You are an expert medical translator specializing in English to Bangla (Bengali) translation 
for the Bangladesh medical context. You have deep knowledge of:

1. Bangladesh medical education terminology (MBBS curriculum)
2. Standard Bangla medical vocabulary used in Bangladeshi hospitals and clinics
3. The difference between Bangladesh Bangla and West Bengal (Kolkata) Bangla dialects

CRITICAL TRANSLATION RULES:

1. **Use Bangladesh Bangla (বাংলাদেশি বাংলা)**, not Kolkata/West Bengal dialect
   - Example: Use "হাসপাতাল" not "হসপিটাল" for hospital

2. **Medical terms:** Follow Bangladesh medical education conventions:
   - Keep widely-used English medical terms in English where Bangladeshi doctors commonly do so
     (e.g., "ECG", "CT scan", "MRI", "X-ray", "hemoglobin", "creatinine")
   - Translate medical concepts that have established Bangla equivalents
     (e.g., "blood pressure" → "রক্তচাপ", "fever" → "জ্বর", "pain" → "ব্যথা")
   - For drug names: Keep the generic drug name in English (e.g., "hydrochlorothiazide", "omeprazole")
   - For disease names: Use Bangla if commonly known (e.g., "diabetes" → "ডায়াবেটিস"), 
     otherwise keep English with Bangla transliteration

3. **Lab values and units:** Keep numerical values and units in English/Arabic numerals
   - Example: "Hemoglobin 9.2 g/dL" → "Hemoglobin 9.2 g/dL"

4. **Clinical accuracy:** The medical meaning must be EXACTLY preserved. 
   Never simplify, omit, or alter any clinical detail.

5. **Natural Bangla:** The translation should read naturally to a Bangladeshi medical professional,
   not like a word-for-word machine translation.

6. **Answer options:** Translate each option maintaining the same letter labels (A, B, C, D).
   Keep technical medical terms consistent with the question translation.

7. **Gender-neutral language:** The source vignettes use gender-neutral language (they/them/patient).
   In Bangla, maintain this neutrality where possible. Use "রোগী" (patient) instead of 
   gender-specific pronouns. If Bangla grammar requires a pronoun, use "তিনি" (they/formal).
"""

USER_PROMPT_TEMPLATE = """Translate the following medical vignette from English to Bangla (Bangladesh context).

Return your response as a JSON object with EXACTLY this structure:
{{
    "question_bangla": "<translated question in Bangla>",
    "options_bangla": {{
        "A": "<translated option A>",
        "B": "<translated option B>",
        "C": "<translated option C>",
        "D": "<translated option D>"
    }},
    "answer_bangla": "<translated answer text in Bangla>",
    "translation_notes": "<any notes about translation choices, e.g., terms kept in English>"
}}

IMPORTANT: Return ONLY the JSON object, no markdown formatting or code blocks.

---

**Vignette ID:** {vignette_id}

**English Question:**
{question}

**English Options:**
A: {option_a}
B: {option_b}
C: {option_c}
D: {option_d}

**English Answer:** {answer}
"""


# ============================================================
# TRANSLATION FUNCTIONS
# ============================================================

def setup_gemini():
    """Configure Gemini API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 60)
        print("ERROR: GOOGLE_API_KEY not found!")
        print()
        print("To get a free API key:")
        print("1. Go to https://aistudio.google.com/apikey")
        print("2. Click 'Create API Key'")
        print("3. Create a .env file in the project root with:")
        print("   GOOGLE_API_KEY=your_key_here")
        print("=" * 60)
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.2,  # Low temperature for consistent translation
            "top_p": 0.95,
            "max_output_tokens": 4096,
            "response_mime_type": "application/json",  # Force JSON output
        },
        system_instruction=SYSTEM_PROMPT,
    )
    
    return model


def translate_vignette(model, vignette, retry_count=0):
    """
    Translate a single vignette using Gemini.
    
    Args:
        model: Gemini GenerativeModel instance
        vignette: Dict with English vignette data
        retry_count: Current retry attempt
    
    Returns:
        Dict with translation results, or None if failed
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        vignette_id=vignette['vignette_id'],
        question=vignette['question'],
        option_a=vignette['options']['A'],
        option_b=vignette['options']['B'],
        option_c=vignette['options']['C'],
        option_d=vignette['options']['D'],
        answer=vignette['answer'],
    )
    
    try:
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()
        
        translation = json.loads(response_text)
        
        # Validate required fields
        required_fields = ['question_bangla', 'options_bangla', 'answer_bangla']
        for field in required_fields:
            if field not in translation:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate options
        for key in ['A', 'B', 'C', 'D']:
            if key not in translation['options_bangla']:
                raise ValueError(f"Missing option {key} in translation")
        
        return translation
        
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"    ⚠ Error: {e}. Retrying in {RETRY_DELAY}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
            return translate_vignette(model, vignette, retry_count + 1)
        else:
            print(f"    ✗ Failed after {MAX_RETRIES} retries: {e}")
            return None


def build_translated_vignette(original, translation):
    """
    Combine original English vignette with Bangla translation.
    
    Preserves all original fields and adds Bangla translations.
    """
    return {
        # Original fields
        "vignette_id": original["vignette_id"],
        "category": original["category"],
        "category_method": original["category_method"],
        
        # English (original)
        "question_en": original["question"],
        "options_en": original["options"],
        "answer_en": original["answer"],
        "answer_idx": original["answer_idx"],
        
        # Bangla (translated)
        "question_bn": translation["question_bangla"],
        "options_bn": translation["options_bangla"],
        "answer_bn": translation["answer_bangla"],
        
        # Metadata
        "translation_notes": translation.get("translation_notes", ""),
        "translation_model": MODEL_NAME,
        "translation_timestamp": datetime.now().isoformat(),
    }


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Pilot Translation (English → Bangla)")
    print(f"Model: {MODEL_NAME}")
    print(f"Input: {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 60)
    
    # Load input data
    print(f"\n📂 Loading pilot vignettes...")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        vignettes = json.load(f)
    print(f"   Loaded {len(vignettes)} vignettes")
    
    # Setup output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for existing partial progress
    translated = []
    completed_ids = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            translated = json.load(f)
            completed_ids = {v['vignette_id'] for v in translated}
        print(f"   Found {len(translated)} existing translations (resuming)")
    
    remaining = [v for v in vignettes if v['vignette_id'] not in completed_ids]
    
    if not remaining:
        print("\n✓ All vignettes already translated!")
        return
    
    print(f"   Translating {len(remaining)} remaining vignettes...")
    
    # Setup Gemini
    print(f"\n🔑 Configuring Gemini API...")
    model = setup_gemini()
    print(f"   Model: {MODEL_NAME}")
    
    # Translation loop
    print(f"\n🔄 Starting translation...\n")
    
    translation_log = []
    failed = []
    
    for i, vignette in enumerate(remaining):
        vid = vignette['vignette_id']
        print(f"  [{i+1}/{len(remaining)}] Translating {vid}...", end=" ", flush=True)
        
        start_time = time.time()
        translation = translate_vignette(model, vignette)
        elapsed = time.time() - start_time
        
        if translation:
            # Build combined record
            combined = build_translated_vignette(vignette, translation)
            translated.append(combined)
            
            print(f"✓ ({elapsed:.1f}s)")
            
            # Log entry
            translation_log.append({
                "vignette_id": vid,
                "status": "success",
                "elapsed_seconds": round(elapsed, 2),
                "timestamp": datetime.now().isoformat(),
            })
            
            # Save progress after each translation (resume-safe)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(translated, f, ensure_ascii=False, indent=2)
            
        else:
            print(f"✗ FAILED")
            failed.append(vid)
            translation_log.append({
                "vignette_id": vid,
                "status": "failed",
                "elapsed_seconds": round(elapsed, 2),
                "timestamp": datetime.now().isoformat(),
            })
        
        # Rate limiting
        if i < len(remaining) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save final output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)
    
    # Save translation log
    log_data = {
        "run_timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "total_vignettes": len(vignettes),
        "translated": len(translated),
        "failed": len(failed),
        "failed_ids": failed,
        "details": translation_log,
    }
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"TRANSLATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  ✓ Translated: {len(translated)}/{len(vignettes)}")
    if failed:
        print(f"  ✗ Failed: {len(failed)} — {failed}")
    print(f"  📁 Output: {OUTPUT_PATH}")
    print(f"  📋 Log: {LOG_PATH}")
    
    # Cost estimate
    # Gemini 2.0 Flash: ~$0.10/1M input tokens, ~$0.40/1M output tokens
    avg_input_tokens = 500  # per vignette
    avg_output_tokens = 800  # per translation
    total_input = avg_input_tokens * len(vignettes) + len(SYSTEM_PROMPT.split()) * len(vignettes)
    total_output = avg_output_tokens * len(vignettes)
    est_cost = (total_input / 1_000_000 * 0.10) + (total_output / 1_000_000 * 0.40)
    print(f"  💰 Estimated cost: ${est_cost:.4f} (likely within free tier)")


if __name__ == "__main__":
    main()
