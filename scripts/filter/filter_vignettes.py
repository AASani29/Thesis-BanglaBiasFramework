#!/usr/bin/env python3
"""
Filter MedQA questions to select 500 relevant vignettes
Part of BanglaMedBias Project - Stage 1
"""

import json
import re
import random
import sys
from pathlib import Path
from collections import defaultdict, Counter

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set random seed for reproducibility
random.seed(42)

def load_medqa():
    """Load MedQA dataset."""
    medqa_file = project_root / 'data' / 'raw' / 'medqa_usmle_full.json'
    
    if not medqa_file.exists():
        print(f"✗ Error: MedQA file not found at {medqa_file}")
        print("\nPlease run first: python scripts/download/download_medqa.py")
        sys.exit(1)
    
    print("Loading MedQA dataset...")
    with open(medqa_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert dict format to list format
    train_data = data.get('train', data)
    
    if isinstance(train_data, dict) and 'question' in train_data:
        # Convert from dict of arrays to list of dicts
        keys = list(train_data.keys())
        n_items = len(train_data['question'])
        
        train_list = []
        for i in range(n_items):
            item = {key: train_data[key][i] for key in keys}
            train_list.append(item)
        
        return train_list
    
    return train_data

def is_clinical_vignette(question_text):
    """
    Check if question is a clinical vignette.
    
    Criteria:
    - Contains patient presentation
    - Has age mention
    - Describes symptoms or findings
    """
    vignette_patterns = [
        (r'\d+-year-old', 2),  # Age mention (weight: 2)
        (r'\bpatient\b', 1),  # Patient reference
        (r'\bpresents?\b|\bpresenting\b', 2),  # Presentation
        (r'comes? to (the )?(clinic|emergency|hospital|office)', 1),  # Visit
        (r'history of', 1),  # Medical history
        (r'physical examination|examination shows|examination reveals', 1),  # PE
        (r'vital signs?|temperature|blood pressure|pulse', 1)  # Vitals
    ]
    
    q_lower = str(question_text).lower()
    
    score = 0
    for pattern, weight in vignette_patterns:
        if re.search(pattern, q_lower):
            score += weight
    
    # Must score at least 4 points to be considered a vignette
    return score >= 4

def is_demographic_neutral(question_text):
    """
    Check if question can be made demographic-neutral.
    
    Exclude gender-specific conditions:
    - Pregnancy/obstetric
    - Gender-specific organs (prostate, uterus, etc.)
    """
    gender_specific = [
        r'\bpregnancy\b', r'\bpregnant\b', r'\bmaternal\b',
        r'\bmenstruation\b', r'\bmenstrual\b', r'\bmenopause\b',
        r'\bprostate\b', r'\btesticular\b', r'\bspermatogenesis\b',
        r'\bovarian\b', r'\bovary\b', r'\buterine\b', r'\buterus\b',
        r'\bcervical cancer\b', r'\bcervix\b', r'\bvaginal\b',
        r'\blabor and delivery\b', r'\bchildbirth\b',
        r'\bobstetric\b', r'\bgynecolog', r'\bbreast feeding\b',
        r'\bamenorrhea\b', r'\bendometrio'
    ]
    
    q_lower = str(question_text).lower()
    return not any(re.search(pattern, q_lower) for pattern in gender_specific)

def has_sufficient_options(item):
    """Check if question has 4 options."""
    if 'options' not in item:
        return False
    
    options = item['options']
    
    # Handle different option formats
    if isinstance(options, dict):
        return len(options) == 4
    elif isinstance(options, list):
        return len(options) == 4
    
    return False

def is_reasonable_length(question_text):
    """Check if question is reasonable length (not too short or too long)."""
    length = len(str(question_text))
    return 150 <= length <= 2000  # Between 150 and 2000 characters

def categorize_question(question_text):
    """
    Categorize question by primary medical domain.
    
    Returns category string.
    """
    categories = {
        'infectious': {
            'keywords': ['fever', 'infection', 'viral', 'bacterial', 'tuberculosis', 
                        'sepsis', 'pneumonia', 'meningitis', 'dengue', 'malaria',
                        'hiv', 'hepatitis', 'abscess'],
            'weight': 1.5  # Higher priority for infectious diseases in Bangladesh
        },
        'diabetes': {
            'keywords': ['diabetes', 'glucose', 'insulin', 'hyperglycemia', 'hypoglycemia',
                        'diabetic', 'blood sugar', 'hemoglobin a1c'],
            'weight': 1.3
        },
        'cardiovascular': {
            'keywords': ['heart', 'cardiac', 'hypertension', 'blood pressure', 'myocardial', 
                        'arrhythmia', 'chest pain', 'angina', 'coronary', 'heart failure'],
            'weight': 1.2
        },
        'respiratory': {
            'keywords': ['respiratory', 'breathing', 'dyspnea', 'cough', 'asthma', 
                        'copd', 'pulmonary', 'bronchitis', 'lung'],
            'weight': 1.2
        },
        'gastrointestinal': {
            'keywords': ['abdominal', 'stomach', 'intestin', 'diarrhea', 'nausea', 
                        'vomiting', 'hepatitis', 'liver', 'gastric', 'bowel'],
            'weight': 1.0
        },
        'neurological': {
            'keywords': ['neuro', 'brain', 'seizure', 'headache', 'stroke', 'consciousness',
                        'paralysis', 'tremor', 'confusion', 'coma'],
            'weight': 1.0
        },
        'renal': {
            'keywords': ['kidney', 'renal', 'urinary', 'acute kidney', 'dialysis',
                        'creatinine', 'oliguria'],
            'weight': 0.9
        },
        'hematology': {
            'keywords': ['anemia', 'bleeding', 'hemoglobin', 'platelet', 'coagulation',
                        'blood count', 'leukemia'],
            'weight': 0.8
        }
    }
    
    q_lower = str(question_text).lower()
    
    # Score each category
    scores = {}
    for category, info in categories.items():
        keyword_matches = sum(1 for kw in info['keywords'] if kw in q_lower)
        scores[category] = keyword_matches * info['weight']
    
    # Return category with highest score, or 'other' if no matches
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return 'other'

def filter_dataset(data):
    """
    Apply filters to dataset.
    
    Returns filtered list with metadata.
    """
    print("\n" + "=" * 60)
    print("Applying Filters")
    print("=" * 60)
    
    filtered = []
    stats = {
        'total': len(data),
        'clinical_vignettes': 0,
        'demographic_neutral': 0,
        'has_options': 0,
        'reasonable_length': 0,
        'passed_all': 0
    }
    
    print(f"\nProcessing {len(data):,} questions...")
    
    for idx, item in enumerate(data):
        if idx % 1000 == 0:
            print(f"  Progress: {idx:,}/{len(data):,}")
        
        question = item.get('question', '')
        
        # Filter 1: Must be clinical vignette
        if not is_clinical_vignette(question):
            continue
        stats['clinical_vignettes'] += 1
        
        # Filter 2: Must be demographically neutral
        if not is_demographic_neutral(question):
            continue
        stats['demographic_neutral'] += 1
        
        # Filter 3: Must have 4 options
        if not has_sufficient_options(item):
            continue
        stats['has_options'] += 1
        
        # Filter 4: Reasonable length
        if not is_reasonable_length(question):
            continue
        stats['reasonable_length'] += 1
        
        # Add category
        category = categorize_question(question)
        item['category'] = category
        
        filtered.append(item)
        stats['passed_all'] += 1
    
    print(f"\n✓ Filtering complete")
    
    return filtered, stats

def stratified_sample(filtered_data, target_total=500):
    """
    Select 500 vignettes using stratified sampling.
    
    Target distribution based on Bangladesh disease burden:
    - Infectious: 30% (150)
    - Diabetes: 20% (100)
    - Cardiovascular: 20% (100)
    - Respiratory: 15% (75)
    - Other conditions: 15% (75)
    """
    print("\n" + "=" * 60)
    print("Stratified Sampling")
    print("=" * 60)
    
    target_distribution = {
        'infectious': 150,
        'diabetes': 100,
        'cardiovascular': 100,
        'respiratory': 75,
        'gastrointestinal': 40,
        'neurological': 20,
        'renal': 15
    }
    
    # Organize by category
    by_category = defaultdict(list)
    for item in filtered_data:
        by_category[item['category']].append(item)
    
    print(f"\nAvailable questions by category:")
    for category in sorted(by_category.keys()):
        count = len(by_category[category])
        target = target_distribution.get(category, 0)
        print(f"  {category:20s}: {count:4,} available (target: {target})")
    
    # Sample from each category
    selected = []
    for category, target in target_distribution.items():
        available = by_category[category]
        
        if len(available) >= target:
            sampled = random.sample(available, target)
            print(f"\n✓ Sampled {len(sampled)} from {category}")
        else:
            # Take all available if less than target
            sampled = available
            print(f"\n⚠ Only {len(available)} available for {category} (target: {target})")
        
        selected.extend(sampled)
    
    # Fill remaining slots from other categories
    remaining = target_total - len(selected)
    if remaining > 0:
        print(f"\n📌 Need {remaining} more to reach {target_total}")
        
        # Pool all unused
        used_ids = {id(item) for item in selected}
        unused = [item for item in filtered_data if id(item) not in used_ids]
        
        if len(unused) >= remaining:
            selected.extend(random.sample(unused, remaining))
            print(f"✓ Added {remaining} from other categories")
        else:
            selected.extend(unused)
            print(f"✓ Added {len(unused)} (all remaining)")
    
    # Shuffle final selection
    random.shuffle(selected)
    
    # Assign IDs
    for idx, item in enumerate(selected, 1):
        item['vignette_id'] = f"MED-{idx:04d}"
    
    print(f"\n✓ Final selection: {len(selected)} vignettes")
    
    return selected

def save_filtered(filtered_data, stats):
    """Save filtered dataset and statistics."""
    output_dir = project_root / 'data' / 'filtered'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full filtered dataset
    output_file = output_dir / 'medqa_filtered_all.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(filtered_data):,} filtered vignettes")
    print(f"  File: {output_file}")
    
    # Save statistics
    stats_dir = project_root / 'outputs' / 'reports'
    stats_dir.mkdir(parents=True, exist_ok=True)
    
    stats_file = stats_dir / 'stage1_filtering_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n✓ Saved filtering statistics")
    print(f"  File: {stats_file}")

def save_selected(selected_data):
    """Save selected 600 vignettes."""
    output_dir = project_root / 'data' / 'filtered'
    output_file = output_dir / 'medqa_selected_600.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_data, f, indent=2, ensure_ascii=False)
    
    # Category breakdown
    category_counts = Counter(item['category'] for item in selected_data)
    
    print(f"\n✓ Selected {len(selected_data)} vignettes")
    print(f"  File: {output_file}")
    print(f"\n  Final category breakdown:")
    for category, count in category_counts.most_common():
        print(f"    {category:20s}: {count:3} ({count/len(selected_data)*100:.1f}%)")

def print_statistics(stats):
    """Print filtering statistics."""
    print("\n" + "=" * 60)
    print("FILTERING STATISTICS")
    print("=" * 60)
    
    total = stats['total']
    
    print(f"\nTotal questions processed: {total:,}")
    print(f"\nFilter Results:")
    print(f"  Clinical vignettes:     {stats['clinical_vignettes']:5,} ({stats['clinical_vignettes']/total*100:5.1f}%)")
    print(f"  Demographic neutral:    {stats['demographic_neutral']:5,} ({stats['demographic_neutral']/total*100:5.1f}%)")
    print(f"  Has 4 options:          {stats['has_options']:5,} ({stats['has_options']/total*100:5.1f}%)")
    print(f"  Reasonable length:      {stats['reasonable_length']:5,} ({stats['reasonable_length']/total*100:5.1f}%)")
    print(f"\n✓ Final filtered:         {stats['passed_all']:5,} ({stats['passed_all']/total*100:5.1f}%)")

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Vignette Filtering & Selection")
    print("Stage 1: Dataset Preparation")
    print("=" * 60)
    
    # Load data
    data = load_medqa()
    print(f"✓ Loaded {len(data):,} questions")
    
    # Apply filters
    filtered, stats = filter_dataset(data)
    
    # Print statistics
    print_statistics(stats)
    
    # Save filtered dataset
    save_filtered(filtered, stats)
    
    # Check if we have enough for stratified sampling
    if len(filtered) < 600:
        print(f"\n✗ Warning: Only {len(filtered)} vignettes after filtering")
        print(f"  Need at least 600 for target selection")
        print(f"  Consider relaxing filter criteria")
        return
    
    # Stratified sampling
    selected = stratified_sample(filtered, target_total=600)
    save_selected(selected)
    
    print("\n" + "=" * 60)
    print("✓ Filtering & Selection Complete!")
    print("=" * 60)
    print("\nOutput files:")
    print(f"  1. All filtered: data/filtered/medqa_filtered_all.json")
    print(f"  2. Selected 600: data/filtered/medqa_selected_600.json")
    print(f"  3. Statistics:   outputs/reports/stage1_filtering_stats.json")
    print("\nNext step:")
    print("  python scripts/filter/quality_check.py")

if __name__ == "__main__":
    main()
