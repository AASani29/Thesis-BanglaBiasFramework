#!/usr/bin/env python3
"""
Re-categorize vignettes using improved method based on diagnosis/answer
Part of BanglaMedBias Project - Stage 1 Improvement
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def categorize_by_diagnosis(answer_text, question_text):
    """
    Improved categorization using the actual diagnosis (answer field).
    Falls back to question text if answer is not informative enough.
    """
    
    # Combine answer and question for context
    combined_text = f"{answer_text} {question_text}".lower()
    
    # More sophisticated category definitions with diagnosis-specific terms
    categories = {
        'infectious': {
            'primary': [
                'infection', 'bacterial', 'viral', 'fungal', 'parasitic',
                'sepsis', 'pneumonia', 'meningitis', 'tuberculosis', 'tb',
                'abscess', 'cellulitis', 'mrsa', 'hiv', 'aids',
                'hepatitis', 'influenza', 'rabies', 'malaria', 'dengue',
                'covid', 'coronavirus', 'antibiotic', 'antimicrobial',
                'vaccine', 'immunoglobulin', 'gonococcal', 'chlamydia',
                'syphilis', 'herpes', 'candida', 'thrush', 'streptococcus',
                'staphylococcus', 'e. coli', 'salmonella', 'legionella'
            ],
            'secondary': ['fever', 'cough with fever', 'sore throat']
        },
        'diabetes': {
            'primary': [
                'diabetes', 'diabetic', 'insulin', 'dka', 'ketoacidosis',
                'hyperglycemia', 'hypoglycemia', 'blood sugar', 'glucose control',
                'metformin', 'sulfonylurea', 'pioglitazone', 'glipizide',
                'hba1c', 'type 1 diabetes', 'type 2 diabetes', 'diabetic ketoacidosis'
            ],
            'secondary': ['glycogen depletion']
        },
        'cardiovascular': {
            'primary': [
                'myocardial infarction', 'heart attack', 'angina', 'coronary',
                'arrhythmia', 'atrial fibrillation', 'heart failure', 'chf',
                'cardiomyopathy', 'hypertension crisis', 'stroke', 'infarct',
                'embolism', 'thrombosis', 'vein obstruction', 'arterial',
                'cardiac', 'endocarditis', 'pericarditis', 'aortic'
            ],
            'secondary': ['chest pain', 'blood pressure', 'hypertension']
        },
        'respiratory': {
            'primary': [
                'asthma', 'copd', 'bronchitis', 'emphysema', 'pulmonary',
                'respiratory failure', 'hypoxia', 'sleep apnea',
                'pulmonary embolism', 'pleural effusion', 'pneumothorax',
                'lung cancer', 'respiratory distress', 'dyspnea',
                'nicotinic acid', 'niacin deficiency', 'pellagra'
            ],
            'secondary': ['cough', 'shortness of breath', 'breathing']
        },
        'gastrointestinal': {
            'primary': [
                'appendicitis', 'cholecystitis', 'pancreatitis', 'cirrhosis',
                'ibd', 'crohn', 'ulcerative colitis', 'diverticulitis',
                'bowel obstruction', 'peptic ulcer', 'gastritis',
                'esophageal', 'liver disease', 'hepatomegaly',
                'squamous cell carcinoma', 'gi bleed', 'hemorrhage',
                'ceruloplasmin', 'wilson', 'celiac', 'malabsorption',
                'increase fiber'
            ],
            'secondary': ['abdominal pain', 'nausea', 'vomiting', 'diarrhea']
        },
        'neurological': {
            'primary': [
                'seizure', 'epilepsy', 'stroke', 'tia', 'cerebral',
                'meningitis', 'encephalitis', 'multiple sclerosis', 'ms',
                'parkinson', 'dementia', 'alzheimer', 'headache severe',
                'migraine', 'brain tumor', 'concussion', 'neuropathy',
                'guillain-barre', 'myasthenia gravis', 'confusion',
                'altered mental status', 'tremor', 'paralysis',
                'osmotic myelinolysis', 'wernicke', 'fluoxetine',
                'posterior cerebral artery'
            ],
            'secondary': ['headache', 'dizziness']
        },
        'renal': {
            'primary': [
                'acute kidney injury', 'chronic kidney disease', 'ckd',
                'nephrotic syndrome', 'nephritic syndrome', 'glomerulonephritis',
                'renal failure', 'dialysis', 'kidney transplant',
                'pyelonephritis', 'renal calculi', 'kidney stone',
                'uremia', 'hyperkalemia', 'urinary tract infection'
            ],
            'secondary': ['creatinine', 'kidney']
        },
        'hematology': {
            'primary': [
                'anemia', 'iron deficiency', 'b12 deficiency', 'folate',
                'sickle cell', 'thalassemia', 'leukemia', 'lymphoma',
                'multiple myeloma', 'thrombocytopenia', 'hemophilia',
                'von willebrand', 'dic', 'coagulopathy', 'neutrophil',
                'transfusion reaction', 'hypersensitivity reaction to transfusion'
            ],
            'secondary': ['bleeding', 'bruising', 'hemoglobin']
        },
        'endocrine': {
            'primary': [
                'thyroid', 'hyperthyroidism', 'hypothyroidism', 'cushings',
                'addison', 'pheochromocytoma', 'acromegaly',
                'growth hormone', 'prolactinoma', 'thyroid storm',
                'vitamin deficiency', 'water soluble vitamin'
            ],
            'secondary': []
        },
        'psychiatric': {
            'primary': [
                'depression', 'anxiety', 'schizophrenia', 'bipolar',
                'psychosis', 'mania', 'ocd', 'ptsd', 'panic disorder',
                'generalized anxiety', 'social phobia', 'folie',
                'buspirone', 'clonazepam', 'ssri'
            ],
            'secondary': []
        },
        'rheumatology': {
            'primary': [
                'rheumatoid arthritis', 'osteoarthritis', 'gout',
                'lupus', 'sle', 'scleroderma', 'polymyalgia',
                'temporal arteritis', 'vasculitis', 'arthritis',
                'erythrocyte sedimentation', 'esr', 'reactive arthritis',
                'patellofemoral pain'
            ],
            'secondary': ['joint pain', 'arthralgia']
        },
        'dermatology': {
            'primary': [
                'skin cancer', 'melanoma', 'basal cell', 'squamous cell',
                'eczema', 'psoriasis', 'dermatitis', 'rash',
                'urticaria', 'cellulitis skin', 'abscess skin',
                'photosensitivity', 'trimethoprim-sulfamethoxazole'
            ],
            'secondary': []
        },
        'pharmacology': {
            'primary': [
                'drug interaction', 'adverse effect', 'toxicity',
                'overdose', 'pharmacokinetics', 'steady state',
                'vancomycin', 'warfarin', 'decreased uric acid',
                'arabinosyltransferase', 'griseofulvin', 'penicillamine',
                'adipokines'
            ],
            'secondary': []
        }
    }
    
    # Score each category
    scores = {}
    for category, keywords in categories.items():
        score = 0
        
        # Check primary keywords (high weight)
        for keyword in keywords['primary']:
            if keyword in combined_text:
                score += 3  # High weight for primary diagnostic terms
        
        # Check secondary keywords (low weight, only if no primary match)
        if score == 0 and 'secondary' in keywords:
            for keyword in keywords['secondary']:
                if keyword in combined_text:
                    score += 0.5  # Low weight for secondary terms
        
        scores[category] = score
    
    # Return category with highest score
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)
    
    return 'other'

def recategorize_vignettes(input_file, output_file):
    """Re-categorize all vignettes and save results."""
    print("\n" + "=" * 60)
    print("Re-categorizing Vignettes with Improved Method")
    print("=" * 60)
    
    # Load existing vignettes
    print(f"\nLoading vignettes from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        vignettes = json.load(f)
    
    print(f"✓ Loaded {len(vignettes)} vignettes")
    
    # Track changes
    changes = {
        'total': len(vignettes),
        'changed': 0,
        'unchanged': 0,
        'changes_detail': []
    }
    
    old_categories = Counter()
    new_categories = Counter()
    
    # Re-categorize each vignette
    print("\nRe-categorizing based on diagnosis...")
    for vignette in vignettes:
        old_category = vignette.get('category', 'unknown')
        answer = vignette.get('answer', '')
        question = vignette.get('question', '')
        
        # Get new category
        new_category = categorize_by_diagnosis(answer, question)
        
        # Track statistics
        old_categories[old_category] += 1
        new_categories[new_category] += 1
        
        # Check if changed
        if old_category != new_category:
            changes['changed'] += 1
            changes['changes_detail'].append({
                'id': vignette['vignette_id'],
                'old': old_category,
                'new': new_category,
                'answer': answer[:80] + '...' if len(answer) > 80 else answer
            })
        else:
            changes['unchanged'] += 1
        
        # Update category
        vignette['category'] = new_category
        vignette['category_method'] = 'diagnosis-based'
    
    # Save re-categorized vignettes
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vignettes, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(vignettes)} vignettes")
    
    return changes, old_categories, new_categories

def generate_comparison_report(changes, old_categories, new_categories):
    """Generate detailed comparison report."""
    print("\n" + "=" * 60)
    print("RECATEGORIZATION SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal vignettes: {changes['total']}")
    print(f"Changed: {changes['changed']} ({changes['changed']/changes['total']*100:.1f}%)")
    print(f"Unchanged: {changes['unchanged']} ({changes['unchanged']/changes['total']*100:.1f}%)")
    
    # Category distribution comparison
    print("\n" + "=" * 60)
    print("CATEGORY DISTRIBUTION COMPARISON")
    print("=" * 60)
    print(f"\n{'Category':<20} {'Old Count':>10} {'New Count':>10} {'Change':>10}")
    print("-" * 60)
    
    all_categories = sorted(set(list(old_categories.keys()) + list(new_categories.keys())))
    for category in all_categories:
        old_count = old_categories.get(category, 0)
        new_count = new_categories.get(category, 0)
        change = new_count - old_count
        change_str = f"+{change}" if change > 0 else str(change)
        print(f"{category:<20} {old_count:>10} {new_count:>10} {change_str:>10}")
    
    # Show sample changes
    if changes['changes_detail']:
        print("\n" + "=" * 60)
        print(f"SAMPLE CHANGES (showing first 20 of {len(changes['changes_detail'])})")
        print("=" * 60)
        
        for change in changes['changes_detail'][:20]:
            print(f"\n{change['id']}:")
            print(f"  Old: {change['old']}")
            print(f"  New: {change['new']}")
            print(f"  Diagnosis: {change['answer']}")
    
    # Save detailed report
    report_file = project_root / 'outputs' / 'reports' / 'recategorization_report.txt'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("RECATEGORIZATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total vignettes: {changes['total']}\n")
        f.write(f"Changed: {changes['changed']} ({changes['changed']/changes['total']*100:.1f}%)\n")
        f.write(f"Unchanged: {changes['unchanged']} ({changes['unchanged']/changes['total']*100:.1f}%)\n\n")
        
        f.write("CATEGORY DISTRIBUTION:\n")
        f.write("-" * 60 + "\n")
        for category, count in new_categories.most_common():
            old_count = old_categories.get(category, 0)
            f.write(f"{category:<20}: {count:>3} (was: {old_count})\n")
        
        f.write("\n\nALL CHANGES:\n")
        f.write("-" * 60 + "\n")
        for change in changes['changes_detail']:
            f.write(f"\n{change['id']}: {change['old']} → {change['new']}\n")
            f.write(f"  Diagnosis: {change['answer']}\n")
    
    print(f"\n✓ Detailed report saved to: {report_file}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Vignette Re-categorization")
    print("Improved Method: Diagnosis-Based Classification")
    print("=" * 60)
    
    # File paths
    input_file = project_root / 'data' / 'filtered' / 'medqa_selected_600.json'
    output_file = project_root / 'data' / 'filtered' / 'medqa_selected_600_recategorized.json'
    
    if not input_file.exists():
        print(f"\n✗ Error: Input file not found at {input_file}")
        print("Please run filter_vignettes.py first.")
        sys.exit(1)
    
    # Re-categorize
    changes, old_categories, new_categories = recategorize_vignettes(input_file, output_file)
    
    # Generate report
    generate_comparison_report(changes, old_categories, new_categories)
    
    print("\n" + "=" * 60)
    print("✓ Re-categorization Complete!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  1. Re-categorized data: {output_file}")
    print(f"  2. Comparison report: outputs/reports/recategorization_report.txt")
    print(f"\nNext steps:")
    print(f"  1. Review the comparison report")
    print(f"  2. If satisfied, replace original file:")
    print(f"     Copy {output_file.name}")
    print(f"     to   medqa_selected_600.json")

if __name__ == "__main__":
    main()
