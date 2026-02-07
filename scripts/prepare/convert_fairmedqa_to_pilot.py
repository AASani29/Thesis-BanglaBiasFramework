#!/usr/bin/env python3
"""
Convert 50 samples from FairMedQA to MedQA format for pilot testing
Part of BanglaMedBias Project - Pilot Phase
"""

import json
import random
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import categorization function from recategorize script
sys.path.insert(0, str(project_root / 'scripts' / 'filter'))
from recategorize_vignettes import categorize_by_diagnosis

# Set random seed for reproducibility
random.seed(42)

def convert_fairmedqa_to_medqa(fairmedqa_item, pilot_id):
    """
    Convert FairMedQA format to MedQA format.
    
    FairMedQA format:
    - question_id, desensitized_question, options, answer, answer_idx
    
    MedQA format:
    - vignette_id, question, options, answer, answer_idx, category, category_method
    """
    
    # Use desensitized question (demographic-neutral version)
    question = fairmedqa_item['desensitized_question']
    answer = fairmedqa_item['answer']
    
    # Categorize using our existing method
    category = categorize_by_diagnosis(answer, question)
    
    return {
        'vignette_id': f'PILOT-{pilot_id:04d}',
        'question': question,
        'options': fairmedqa_item['options'],
        'answer': answer,
        'answer_idx': fairmedqa_item['answer_idx'],
        'category': category,
        'category_method': 'diagnosis-based'
    }

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - FairMedQA to Pilot Dataset Conversion")
    print("Converting 50 samples for pilot testing")
    print("=" * 60)
    
    # Default path (from Downloads)
    default_path = r"C:\Users\bashi\Downloads\FairMedQA-Materials\FairMedQA-Materials\1_FairMedQA_Dataset\FairMedQA_Dataset.jsonl"
    
    print(f"\nDefault path: {default_path}")
    use_default = input("Use this path? (y/n): ").strip().lower()
    
    if use_default == 'y':
        fairmedqa_path = Path(default_path)
    else:
        fairmedqa_file = input("\nEnter full path to FairMedQA_Dataset.jsonl: ").strip().strip('"')
        fairmedqa_path = Path(fairmedqa_file)
    
    if not fairmedqa_path.exists():
        print(f"\n✗ Error: File not found at {fairmedqa_path}")
        sys.exit(1)
    
    # Load all FairMedQA questions
    print(f"\nLoading FairMedQA dataset from {fairmedqa_path}...")
    all_questions = []
    with open(fairmedqa_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                all_questions.append(json.loads(line))
    
    print(f"✓ Loaded {len(all_questions)} questions from FairMedQA")
    
    # Sample 50 questions randomly
    if len(all_questions) < 50:
        print(f"\n✗ Warning: Only {len(all_questions)} questions available")
        sample_size = len(all_questions)
    else:
        sample_size = 50
    
    sampled_questions = random.sample(all_questions, sample_size)
    print(f"✓ Randomly selected {sample_size} questions")
    
    # Convert to MedQA format
    print("\nConverting to MedQA format...")
    pilot_dataset = []
    for idx, item in enumerate(sampled_questions, start=1):
        converted = convert_fairmedqa_to_medqa(item, idx)
        pilot_dataset.append(converted)
        
        if idx % 10 == 0:
            print(f"  Converted {idx}/{sample_size}...")
    
    print(f"✓ Converted {len(pilot_dataset)} questions")
    
    # Show category distribution
    from collections import Counter
    category_counts = Counter(item['category'] for item in pilot_dataset)
    
    print("\nCategory distribution:")
    for category, count in category_counts.most_common():
        print(f"  {category:20s}: {count:2d} ({count/len(pilot_dataset)*100:.1f}%)")
    
    # Save to output file
    output_dir = project_root / 'data' / 'pilot'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'pilot_50_from_fairmedqa.json'
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pilot_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(pilot_dataset)} pilot vignettes")
    
    print("\n" + "=" * 60)
    print("✓ Conversion Complete!")
    print("=" * 60)
    print(f"\nOutput file: {output_file}")
    print(f"\nNext steps:")
    print("1. Review the pilot dataset")
    print("2. Translate these 50 vignettes to Bangla (manual or GPT-4)")
    print("3. Create demographic variants (6 per vignette = 300 test cases)")
    print("4. Test with GPT-4 and Claude to check for bias signals")
    print("5. Analyze results before proceeding to full 600 vignette translation")

if __name__ == "__main__":
    main()
