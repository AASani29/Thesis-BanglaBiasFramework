#!/usr/bin/env python3
"""
Explore MedQA dataset structure and statistics
Part of BanglaMedBias Project - Stage 1
"""

import json
import sys
from pathlib import Path
from collections import Counter
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_medqa():
    """Load MedQA dataset."""
    medqa_file = project_root / 'data' / 'raw' / 'medqa_usmle_full.json'
    
    if not medqa_file.exists():
        print(f"✗ Error: MedQA file not found at {medqa_file}")
        print("\nPlease run first: python scripts/download/download_medqa.py")
        sys.exit(1)
    
    print(f"Loading dataset from {medqa_file}...")
    with open(medqa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Use train split
    return data.get('train', data)

def analyze_structure(data):
    """Analyze dataset structure."""
    print("\n" + "=" * 60)
    print("DATASET STRUCTURE ANALYSIS")
    print("=" * 60)
    
    # Convert dict format to list if needed
    if isinstance(data, dict) and 'question' in data:
        # Dictionary format with arrays
        fields = list(data.keys())
        total = len(data['question'])
        sample_idx = 0
        sample = {key: data[key][sample_idx] for key in fields}
    else:
        # List format
        fields = list(data[0].keys()) if data else []
        total = len(data)
        sample = data[0] if data else {}
    
    print(f"\nTotal questions: {total:,}")
    print(f"Fields available: {', '.join(fields)}")
    
    print("\nSample question structure:")
    print(json.dumps(sample, indent=2, ensure_ascii=False)[:800] + "\n...")
    
    return total

def analyze_questions(data):
    """Analyze question characteristics."""
    print("\n" + "=" * 60)
    print("QUESTION CHARACTERISTICS")
    print("=" * 60)
    
    # Convert to list of questions
    if isinstance(data, dict) and 'question' in data:
        questions = data['question']
    else:
        questions = [q.get('question', '') for q in data]
    
    # Length analysis
    lengths = [len(str(q)) for q in questions]
    lengths_sorted = sorted(lengths)
    
    print(f"\nQuestion Length Statistics:")
    print(f"  Average: {sum(lengths)/len(lengths):.0f} characters")
    print(f"  Min: {min(lengths)} characters")
    print(f"  Max: {max(lengths)} characters")
    print(f"  Median: {lengths_sorted[len(lengths_sorted)//2]} characters")
    print(f"  25th percentile: {lengths_sorted[len(lengths_sorted)//4]} characters")
    print(f"  75th percentile: {lengths_sorted[3*len(lengths_sorted)//4]} characters")
    
    # Clinical vignette detection
    vignette_indicators = [
        r'\d+-year-old',
        r'\bpatient\b',
        r'\bpresents?\b',
        r'history of',
        r'physical examination'
    ]
    
    vignette_count = 0
    for q in questions:
        q_str = str(q).lower()
        matches = sum(1 for pattern in vignette_indicators if re.search(pattern, q_str))
        if matches >= 2:  # At least 2 indicators
            vignette_count += 1
    
    print(f"\nClinical Vignettes (estimated): {vignette_count:,} ({vignette_count/len(questions)*100:.1f}%)")
    
    # Show sample vignette
    for q in questions[:50]:
        q_str = str(q).lower()
        matches = sum(1 for pattern in vignette_indicators if re.search(pattern, q_str))
        if matches >= 3:
            print(f"\nSample clinical vignette:")
            print(f"{str(q)[:300]}...")
            break

def analyze_demographics(data):
    """Analyze demographic mentions."""
    print("\n" + "=" * 60)
    print("DEMOGRAPHIC ANALYSIS")
    print("=" * 60)
    
    if isinstance(data, dict) and 'question' in data:
        questions = data['question']
    else:
        questions = [q.get('question', '') for q in data]
    
    questions_str = [str(q).lower() for q in questions]
    
    # Gender mentions
    male_patterns = [r'\bman\b', r'\bmale\b', r'\bhe\b', r'\bhis\b', r'\bhim\b']
    female_patterns = [r'\bwoman\b', r'\bfemale\b', r'\bshe\b', r'\bher\b']
    
    male_count = sum(1 for q in questions_str if any(re.search(p, q) for p in male_patterns))
    female_count = sum(1 for q in questions_str if any(re.search(p, q) for p in female_patterns))
    
    print(f"\nGender Mentions:")
    print(f"  Male indicators: {male_count:,} ({male_count/len(questions)*100:.1f}%)")
    print(f"  Female indicators: {female_count:,} ({female_count/len(questions)*100:.1f}%)")
    
    # Age mentions
    age_mentions = []
    for q in questions_str:
        match = re.search(r'(\d+)-year-old', q)
        if match:
            age_mentions.append(int(match.group(1)))
    
    if age_mentions:
        print(f"\nAge Statistics:")
        print(f"  Questions with age: {len(age_mentions):,} ({len(age_mentions)/len(questions)*100:.1f}%)")
        print(f"  Average age: {sum(age_mentions)/len(age_mentions):.1f} years")
        print(f"  Age range: {min(age_mentions)}-{max(age_mentions)} years")
        
        # Age distribution
        age_groups = {
            'Pediatric (0-18)': sum(1 for a in age_mentions if a <= 18),
            'Young adult (19-40)': sum(1 for a in age_mentions if 19 <= a <= 40),
            'Middle age (41-65)': sum(1 for a in age_mentions if 41 <= a <= 65),
            'Elderly (65+)': sum(1 for a in age_mentions if a > 65)
        }
        
        print(f"\n  Age distribution:")
        for group, count in age_groups.items():
            print(f"    {group}: {count:,} ({count/len(age_mentions)*100:.1f}%)")

def categorize_by_topic(data):
    """Categorize questions by medical topic."""
    print("\n" + "=" * 60)
    print("MEDICAL TOPIC CATEGORIZATION")
    print("=" * 60)
    
    if isinstance(data, dict) and 'question' in data:
        questions = data['question']
    else:
        questions = [q.get('question', '') for q in data]
    
    categories = {
        'Infectious Disease': ['infection', 'fever', 'viral', 'bacterial', 'tuberculosis', 
                               'sepsis', 'pneumonia', 'meningitis', 'dengue', 'malaria'],
        'Cardiovascular': ['heart', 'cardiac', 'hypertension', 'blood pressure', 'myocardial',
                          'arrhythmia', 'chest pain', 'angina'],
        'Respiratory': ['respiratory', 'breathing', 'cough', 'asthma', 'copd', 'pulmonary',
                       'dyspnea', 'bronchitis'],
        'Diabetes/Endocrine': ['diabetes', 'glucose', 'insulin', 'thyroid', 'endocrine',
                               'hyperglycemia', 'hypoglycemia'],
        'Gastrointestinal': ['abdominal', 'stomach', 'intestin', 'diarrhea', 'nausea',
                            'vomiting', 'hepatitis', 'liver', 'gastric'],
        'Neurological': ['neuro', 'brain', 'seizure', 'headache', 'stroke', 'consciousness',
                        'paralysis', 'tremor'],
        'Renal': ['kidney', 'renal', 'urinary', 'acute kidney injury', 'dialysis'],
        'Oncology': ['cancer', 'tumor', 'malignancy', 'carcinoma', 'metasta', 'chemotherapy'],
        'Maternal/Obstetric': ['pregnancy', 'pregnant', 'maternal', 'prenatal', 'delivery',
                               'obstetric', 'labor']
    }
    
    category_counts = Counter()
    categorized = []
    
    for q in questions:
        q_lower = str(q).lower()
        found_category = None
        max_matches = 0
        
        for category, keywords in categories.items():
            matches = sum(1 for keyword in keywords if keyword in q_lower)
            if matches > max_matches:
                max_matches = matches
                found_category = category
        
        if found_category:
            category_counts[found_category] += 1
            categorized.append(found_category)
        else:
            categorized.append('Other')
            category_counts['Other'] += 1
    
    print("\nQuestions by Medical Category:")
    for category, count in category_counts.most_common():
        print(f"  {category:25s}: {count:5,} ({count/len(questions)*100:.1f}%)")
    
    return category_counts

def analyze_options(data):
    """Analyze answer options."""
    print("\n" + "=" * 60)
    print("ANSWER OPTIONS ANALYSIS")
    print("=" * 60)
    
    if isinstance(data, dict):
        if 'options' in data:
            # Check structure of options
            sample_options = data['options'][0] if data['options'] else None
            print(f"\nOptions format: {type(sample_options)}")
            
            if isinstance(sample_options, dict):
                option_counts = [len(opts) for opts in data['options']]
                print(f"Average options per question: {sum(option_counts)/len(option_counts):.1f}")
                print(f"Questions with 4 options: {sum(1 for c in option_counts if c == 4):,}")
    
    print("\nNote: Detailed options analysis requires specific dataset structure.")

def generate_exploration_report(stats):
    """Generate exploration summary report."""
    report_file = project_root / 'outputs' / 'reports' / 'stage1_exploration_summary.txt'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MedQA Dataset Exploration Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total questions analyzed: {stats['total']:,}\n")
        f.write(f"Estimated clinical vignettes: {stats.get('vignettes', 'N/A')}\n")
        f.write(f"\nTop medical categories:\n")
        for cat, count in stats.get('categories', {}).most_common(5):
            f.write(f"  - {cat}: {count:,}\n")
    
    print(f"\n✓ Exploration report saved to: {report_file}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Data Exploration Script")
    print("Stage 1: Understanding the Dataset")
    print("=" * 60)
    
    # Load data
    data = load_medqa()
    print("✓ Dataset loaded")
    
    # Run analyses
    total = analyze_structure(data)
    analyze_questions(data)
    analyze_demographics(data)
    category_counts = categorize_by_topic(data)
    analyze_options(data)
    
    # Generate report
    stats = {
        'total': total,
        'categories': category_counts
    }
    generate_exploration_report(stats)
    
    print("\n" + "=" * 60)
    print("✓ Exploration Complete!")
    print("=" * 60)
    print("\nKey Findings:")
    print(f"  • Total questions: {total:,}")
    print(f"  • Multiple medical categories identified")
    print(f"  • Ready for filtering stage")
    print("\nNext step:")
    print("  python scripts/filter/filter_vignettes.py")

if __name__ == "__main__":
    main()
