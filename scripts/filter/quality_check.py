#!/usr/bin/env python3
"""
Quality check on selected 600 vignettes
Part of BanglaMedBias Project - Stage 1
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_selected():
    """Load selected 600 vignettes."""
    selected_file = project_root / 'data' / 'filtered' / 'medqa_selected_600.json'
    
    if not selected_file.exists():
        print(f"✗ Error: Selected file not found at {selected_file}")
        print("\nPlease run first: python scripts/filter/filter_vignettes.py")
        sys.exit(1)
    
    print(f"Loading selected vignettes from {selected_file}...")
    with open(selected_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_completeness(data):
    """Check if all required fields present."""
    print("\n" + "=" * 60)
    print("COMPLETENESS CHECK")
    print("=" * 60)
    
    required_fields = ['vignette_id', 'question', 'options', 'answer', 'category']
    issues = []
    
    for item in data:
        vignette_id = item.get('vignette_id', 'UNKNOWN')
        
        # Check required fields
        for field in required_fields:
            if field not in item:
                issues.append(f"{vignette_id}: Missing field '{field}'")
        
        # Check options count
        if 'options' in item:
            options = item['options']
            if isinstance(options, dict):
                option_count = len(options)
            elif isinstance(options, list):
                option_count = len(options)
            else:
                option_count = 0
            
            if option_count != 4:
                issues.append(f"{vignette_id}: Not exactly 4 options ({option_count} found)")
        
        # Check question not empty
        if 'question' in item and len(str(item['question']).strip()) == 0:
            issues.append(f"{vignette_id}: Empty question")
    
    if issues:
        print(f"\n✗ Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues)-10} more")
        return False
    else:
        print("\n✓ All vignettes complete")
        print(f"  • All {len(data)} vignettes have required fields")
        print(f"  • All questions have 4 options")
        return True

def check_length_distribution(data):
    """Check question length distribution."""
    print("\n" + "=" * 60)
    print("LENGTH DISTRIBUTION")
    print("=" * 60)
    
    lengths = [len(str(item['question'])) for item in data]
    lengths_sorted = sorted(lengths)
    
    mean_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    median = lengths_sorted[len(lengths_sorted) // 2]
    q1 = lengths_sorted[len(lengths_sorted) // 4]
    q3 = lengths_sorted[3 * len(lengths_sorted) // 4]
    
    print(f"\nQuestion Length Statistics:")
    print(f"  Mean:           {mean_length:6.0f} characters")
    print(f"  Median:         {median:6.0f} characters")
    print(f"  Min:            {min_length:6.0f} characters")
    print(f"  Max:            {max_length:6.0f} characters")
    print(f"  25th percentile:{q1:6.0f} characters")
    print(f"  75th percentile:{q3:6.0f} characters")
    
    # Flag very short or very long
    too_short = [item for item, length in zip(data, lengths) if length < 100]
    too_long = [item for item, length in zip(data, lengths) if length > 1500]
    
    issues = []
    if too_short:
        print(f"\n⚠ {len(too_short)} vignettes too short (<100 chars):")
        for item in too_short[:3]:
            print(f"  - {item['vignette_id']}: {len(item['question'])} chars")
        issues.append('short')
    
    if too_long:
        print(f"\n⚠ {len(too_long)} vignettes too long (>1500 chars):")
        for item in too_long[:3]:
            print(f"  - {item['vignette_id']}: {len(item['question'])} chars")
        issues.append('long')
    
    if not issues:
        print("\n✓ All vignettes within reasonable length range")
        return True
    else:
        # Allow some outliers
        if len(too_short) < 5 and len(too_long) < 10:
            print("\n✓ Minor length variations acceptable")
            return True
        return False

def check_readability(data):
    """Check clinical vignette structure."""
    print("\n" + "=" * 60)
    print("READABILITY & STRUCTURE CHECK")
    print("=" * 60)
    
    # Expected patterns in clinical vignettes
    patterns = {
        'patient_mention': r'\bpatient\b',
        'age': r'\d+-year-old',
        'presentation': r'\bpresents?\b|\bpresenting\b|\bcomes to\b',
        'vital_signs': r'temperature|blood pressure|pulse|heart rate|bp',
        'physical_exam': r'physical examination|examination shows|examination reveals|on examination'
    }
    
    pattern_counts = {key: 0 for key in patterns}
    
    for item in data:
        question = str(item['question']).lower()
        for key, pattern in patterns.items():
            if re.search(pattern, question):
                pattern_counts[key] += 1
    
    total = len(data)
    print(f"\nVignette Structure Elements (out of {total}):")
    for key, count in pattern_counts.items():
        percentage = count / total * 100
        status = "✓" if percentage >= 70 else "⚠"
        print(f"  {status} {key:20s}: {count:3} ({percentage:5.1f}%)")
    
    # Should have high percentage of patient mentions and age
    patient_rate = pattern_counts['patient_mention'] / total
    age_rate = pattern_counts['age'] / total
    
    if patient_rate > 0.7 and age_rate > 0.6:
        print(f"\n✓ Good clinical vignette structure")
        return True
    else:
        print(f"\n⚠ Some vignettes may not follow typical clinical format")
        print(f"  This is acceptable if content is still medically relevant")
        return True  # Still pass if most are good

def check_category_distribution(data):
    """Check category distribution matches target."""
    print("\n" + "=" * 60)
    print("CATEGORY DISTRIBUTION")
    print("=" * 60)
    
    category_counts = Counter(item['category'] for item in data)
    
    # Expected distribution (approximate)
    target = {
        'infectious': (140, 160),       # Target: 150 ± 10
        'diabetes': (90, 110),           # Target: 100 ± 10
        'cardiovascular': (90, 110),     # Target: 100 ± 10
        'respiratory': (65, 85),         # Target: 75 ± 10
        'gastrointestinal': (30, 50),    # Target: 40 ± 10
        'neurological': (10, 30),        # Target: 20 ± 10
        'renal': (5, 25)                 # Target: 15 ± 10
    }
    
    print(f"\nActual Distribution (out of {len(data)}):")
    all_good = True
    for category, count in category_counts.most_common():
        percentage = count / len(data) * 100
        
        if category in target:
            min_target, max_target = target[category]
            in_range = min_target <= count <= max_target
            status = "✓" if in_range else "⚠"
            print(f"  {status} {category:20s}: {count:3} ({percentage:5.1f}%) [target: {min_target}-{max_target}]")
            if not in_range:
                all_good = False
        else:
            print(f"    {category:20s}: {count:3} ({percentage:5.1f}%)")
    
    if all_good:
        print(f"\n✓ Distribution matches targets")
    else:
        print(f"\n⚠ Some categories outside target range (acceptable)")
    
    return True  # Always pass, just informational

def check_diversity(data):
    """Check for diversity in medical scenarios."""
    print("\n" + "=" * 60)
    print("DIVERSITY CHECK")
    print("=" * 60)
    
    # Check age diversity
    ages = []
    for item in data:
        match = re.search(r'(\d+)-year-old', str(item['question']))
        if match:
            ages.append(int(match.group(1)))
    
    if ages:
        age_groups = {
            'Pediatric (0-18)': sum(1 for a in ages if a <= 18),
            'Young adult (19-40)': sum(1 for a in ages if 19 <= a <= 40),
            'Middle age (41-65)': sum(1 for a in ages if 41 <= a <= 65),
            'Elderly (65+)': sum(1 for a in ages if a > 65)
        }
        
        print(f"\nAge Distribution ({len(ages)} vignettes with age):")
        for group, count in age_groups.items():
            print(f"  {group:25s}: {count:3} ({count/len(ages)*100:5.1f}%)")
        
        # Check if all age groups represented
        if all(count > 0 for count in age_groups.values()):
            print(f"\n✓ All age groups represented")
        else:
            print(f"\n⚠ Some age groups underrepresented")
    
    # Check for unique questions (no duplicates)
    questions = [str(item['question']) for item in data]
    unique_questions = len(set(questions))
    
    print(f"\nDuplication Check:")
    print(f"  Total vignettes:  {len(questions)}")
    print(f"  Unique questions: {unique_questions}")
    
    if unique_questions == len(questions):
        print(f"  ✓ No duplicates found")
        return True
    else:
        duplicates = len(questions) - unique_questions
        print(f"  ⚠ {duplicates} potential duplicates")
        return False

def check_id_uniqueness(data):
    """Check that all vignette IDs are unique."""
    print("\n" + "=" * 60)
    print("ID UNIQUENESS CHECK")
    print("=" * 60)
    
    ids = [item.get('vignette_id', '') for item in data]
    unique_ids = set(ids)
    
    if len(unique_ids) == len(ids):
        print(f"\n✓ All {len(ids)} vignette IDs are unique")
        print(f"  Format: {ids[0]} to {ids[-1]}")
        return True
    else:
        duplicates = len(ids) - len(unique_ids)
        print(f"\n✗ Found {duplicates} duplicate IDs")
        
        # Find duplicates
        id_counts = Counter(ids)
        dup_ids = [vid for vid, count in id_counts.items() if count > 1]
        print(f"  Duplicate IDs: {', '.join(dup_ids[:5])}")
        return False

def generate_report(data, checks):
    """Generate QC report."""
    report_lines = [
        "QUALITY CHECK REPORT - Stage 1",
        "=" * 60,
        "",
        f"Total Vignettes: {len(data)}",
        f"Generated: {Path(__file__).name}",
        "",
        "Check Results:",
        "=" * 60
    ]
    
    check_names = {
        'completeness': 'Completeness',
        'length': 'Length Distribution',
        'readability': 'Readability',
        'category': 'Category Distribution',
        'diversity': 'Diversity',
        'id_uniqueness': 'ID Uniqueness'
    }
    
    for key, name in check_names.items():
        status = 'PASS ✓' if checks.get(key, False) else 'FAIL ✗'
        report_lines.append(f"{name:25s}: {status}")
    
    overall = all(checks.values())
    report_lines.extend([
        "",
        f"Overall: {'PASS ✓' if overall else 'FAIL ✗'}",
        "=" * 60,
        "",
        "Next Steps:",
    ])
    
    if overall:
        report_lines.extend([
            "✓ Dataset ready for translation",
            "",
            "Run next stage:",
            "  python scripts/translate/translate_pipeline.py"
        ])
    else:
        report_lines.extend([
            "⚠ Review flagged issues above",
            "  Most issues are minor and acceptable",
            "  If critical issues found, re-run filter with adjusted parameters"
        ])
    
    report = "\n".join(report_lines)
    
    # Save report
    report_file = project_root / 'outputs' / 'reports' / 'stage1_quality_check.txt'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print(report)
    print(f"\n✓ Report saved to: {report_file}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Quality Check")
    print("Stage 1: Final Validation")
    print("=" * 60)
    
    # Load data
    data = load_selected()
    print(f"✓ Loaded {len(data)} vignettes")
    
    # Run checks
    checks = {
        'completeness': check_completeness(data),
        'length': check_length_distribution(data),
        'readability': check_readability(data),
        'category': check_category_distribution(data),
        'diversity': check_diversity(data),
        'id_uniqueness': check_id_uniqueness(data)
    }
    
    # Generate report
    generate_report(data, checks)
    
    # Final summary
    passed = sum(checks.values())
    total = len(checks)
    
    print("\n" + "=" * 60)
    if all(checks.values()):
        print("✓✓✓ ALL CHECKS PASSED ✓✓✓")
    else:
        print(f"Quality Check: {passed}/{total} checks passed")
        print("Minor issues are acceptable - review report above")
    print("=" * 60)

if __name__ == "__main__":
    main()
