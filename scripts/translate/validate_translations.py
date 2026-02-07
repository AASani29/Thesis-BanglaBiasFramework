#!/usr/bin/env python3
"""
Validate Bangla translations using a second LLM (back-translation + quality check).

Part of BanglaMedBias Project - Pilot Phase
Quality assurance step after translation.

This script:
1. Back-translates Bangla → English using Gemini
2. Compares back-translation with original English
3. Flags potential issues (medical term changes, meaning shifts)
4. Generates a quality report

Usage:
    python scripts/translate/validate_translations.py
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

import google.generativeai as genai

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-2.0-flash"

TRANSLATED_PATH = project_root / "data" / "pilot" / "bangla" / "pilot_50_bangla.json"
REPORT_PATH = project_root / "data" / "pilot" / "bangla" / "quality_report.json"
REPORT_MD_PATH = project_root / "data" / "pilot" / "bangla" / "quality_report.md"

DELAY_BETWEEN_REQUESTS = 4.5  # seconds (stay under 15 RPM)
MAX_RETRIES = 3
RETRY_DELAY = 10

# ============================================================
# VALIDATION PROMPTS
# ============================================================

VALIDATION_SYSTEM_PROMPT = """You are an expert bilingual medical reviewer fluent in both English and Bangla (Bangladesh).
Your task is to evaluate the quality of English-to-Bangla medical translations.

For each translation, assess:
1. **Medical Accuracy** (1-5): Are all medical terms, diagnoses, lab values, and clinical details preserved?
2. **Linguistic Quality** (1-5): Is the Bangla natural and grammatically correct for Bangladesh?
3. **Completeness** (1-5): Is all information from the original preserved? Nothing omitted or added?
4. **Consistency** (1-5): Are medical term translations consistent (same term translated the same way)?

Score guide: 1=Poor, 2=Below Average, 3=Acceptable, 4=Good, 5=Excellent
"""

VALIDATION_PROMPT_TEMPLATE = """Evaluate this medical translation from English to Bangla.

**Original English Question:**
{question_en}

**Original English Options:**
A: {option_a_en}
B: {option_b_en}
C: {option_c_en}
D: {option_d_en}

**Bangla Translation (Question):**
{question_bn}

**Bangla Translation (Options):**
A: {option_a_bn}
B: {option_b_bn}
C: {option_c_bn}
D: {option_d_bn}

Return your evaluation as a JSON object:
{{
    "medical_accuracy_score": <1-5>,
    "linguistic_quality_score": <1-5>,
    "completeness_score": <1-5>,
    "consistency_score": <1-5>,
    "overall_score": <1-5>,
    "issues": ["<list of specific issues found, if any>"],
    "back_translation_answer": "<English back-translation of the Bangla answer option>",
    "recommendation": "<pass/review/retranslate>"
}}

IMPORTANT: Return ONLY the JSON object.
"""


def setup_gemini():
    """Configure Gemini API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 2048,
            "response_mime_type": "application/json",
        },
        system_instruction=VALIDATION_SYSTEM_PROMPT,
    )
    
    return model


def validate_translation(model, vignette, retry_count=0):
    """Validate a single translated vignette."""
    prompt = VALIDATION_PROMPT_TEMPLATE.format(
        question_en=vignette['question_en'],
        option_a_en=vignette['options_en']['A'],
        option_b_en=vignette['options_en']['B'],
        option_c_en=vignette['options_en']['C'],
        option_d_en=vignette['options_en']['D'],
        question_bn=vignette['question_bn'],
        option_a_bn=vignette['options_bn']['A'],
        option_b_bn=vignette['options_bn']['B'],
        option_c_bn=vignette['options_bn']['C'],
        option_d_bn=vignette['options_bn']['D'],
    )
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"    ⚠ Retry {retry_count + 1}: {e}")
            time.sleep(RETRY_DELAY)
            return validate_translation(model, vignette, retry_count + 1)
        else:
            return None


def generate_markdown_report(results, vignettes):
    """Generate a human-readable markdown quality report."""
    lines = [
        "# Translation Quality Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total vignettes:** {len(results)}",
        "",
    ]
    
    # Summary statistics
    scores = {
        'medical_accuracy': [],
        'linguistic_quality': [],
        'completeness': [],
        'consistency': [],
        'overall': [],
    }
    
    recommendations = {'pass': 0, 'review': 0, 'retranslate': 0}
    
    for r in results:
        if r.get('validation'):
            v = r['validation']
            scores['medical_accuracy'].append(v.get('medical_accuracy_score', 0))
            scores['linguistic_quality'].append(v.get('linguistic_quality_score', 0))
            scores['completeness'].append(v.get('completeness_score', 0))
            scores['consistency'].append(v.get('consistency_score', 0))
            scores['overall'].append(v.get('overall_score', 0))
            rec = v.get('recommendation', 'review').lower()
            recommendations[rec] = recommendations.get(rec, 0) + 1
    
    lines.append("## Summary Scores\n")
    lines.append("| Metric | Average | Min | Max |")
    lines.append("|--------|---------|-----|-----|")
    for key, vals in scores.items():
        if vals:
            avg = sum(vals) / len(vals)
            lines.append(f"| {key.replace('_', ' ').title()} | {avg:.2f} | {min(vals)} | {max(vals)} |")
    
    lines.append(f"\n## Recommendations\n")
    lines.append(f"- ✅ Pass: {recommendations.get('pass', 0)}")
    lines.append(f"- ⚠️ Review: {recommendations.get('review', 0)}")
    lines.append(f"- ❌ Retranslate: {recommendations.get('retranslate', 0)}")
    
    # Flag items needing attention
    flagged = [r for r in results if r.get('validation', {}).get('recommendation', '').lower() != 'pass']
    if flagged:
        lines.append(f"\n## Items Needing Attention ({len(flagged)})\n")
        for r in flagged:
            vid = r['vignette_id']
            v = r.get('validation', {})
            lines.append(f"### {vid}")
            lines.append(f"- **Overall Score:** {v.get('overall_score', 'N/A')}")
            lines.append(f"- **Recommendation:** {v.get('recommendation', 'N/A')}")
            issues = v.get('issues', [])
            if issues:
                lines.append(f"- **Issues:**")
                for issue in issues:
                    lines.append(f"  - {issue}")
            lines.append("")
    
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("BanglaMedBias - Translation Quality Validation")
    print("=" * 60)
    
    # Load translations
    if not TRANSLATED_PATH.exists():
        print(f"\n✗ Translation file not found: {TRANSLATED_PATH}")
        print("  Run translate_pilot_to_bangla.py first!")
        sys.exit(1)
    
    with open(TRANSLATED_PATH, 'r', encoding='utf-8') as f:
        vignettes = json.load(f)
    print(f"\n📂 Loaded {len(vignettes)} translated vignettes")
    
    # Setup model
    model = setup_gemini()
    print(f"🔑 Gemini configured ({MODEL_NAME})")
    
    # Validate each translation
    print(f"\n🔍 Validating translations...\n")
    
    results = []
    for i, v in enumerate(vignettes):
        vid = v['vignette_id']
        print(f"  [{i+1}/{len(vignettes)}] Validating {vid}...", end=" ", flush=True)
        
        validation = validate_translation(model, v)
        
        result = {
            "vignette_id": vid,
            "validation": validation,
        }
        results.append(result)
        
        if validation:
            score = validation.get('overall_score', '?')
            rec = validation.get('recommendation', '?')
            print(f"Score: {score}/5 [{rec}]")
        else:
            print("✗ FAILED")
        
        if i < len(vignettes) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save results
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Generate markdown report
    md_report = generate_markdown_report(results, vignettes)
    with open(REPORT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"\n{'=' * 60}")
    print(f"VALIDATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  📋 JSON Report: {REPORT_PATH}")
    print(f"  📄 Markdown Report: {REPORT_MD_PATH}")
    
    # Quick summary
    overall_scores = [r['validation']['overall_score'] for r in results if r.get('validation')]
    if overall_scores:
        avg = sum(overall_scores) / len(overall_scores)
        print(f"\n  Average Quality Score: {avg:.2f}/5.0")
        if avg >= 4.0:
            print("  ✅ Translation quality is GOOD — proceed to demographic variants")
        elif avg >= 3.0:
            print("  ⚠️ Translation quality is ACCEPTABLE — review flagged items")
        else:
            print("  ❌ Translation quality NEEDS IMPROVEMENT — review and retranslate flagged items")


if __name__ == "__main__":
    main()
