#!/usr/bin/env python3
"""
Download MedQA-USMLE and AMQA datasets
Part of BanglaMedBias Project - Stage 1
"""

import os
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def download_medqa():
    """Download MedQA from HuggingFace."""
    print("\n" + "=" * 60)
    print("Downloading MedQA-USMLE from HuggingFace")
    print("=" * 60)
    
    try:
        from datasets import load_dataset
    except ImportError:
        print("✗ Error: 'datasets' library not installed")
        print("Please run: pip install -r requirements.txt")
        return None
    
    try:
        print("\nFetching dataset from HuggingFace...")
        dataset = load_dataset("GBaker/MedQA-USMLE-4-options")
        
        # Convert to dictionary format for saving
        data = {}
        for split in dataset.keys():
            data[split] = dataset[split].to_dict()
        
        # Ensure output directory exists
        output_dir = project_root / 'data' / 'raw'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        output_file = output_dir / 'medqa_usmle_full.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Count total questions
        total_questions = sum(len(data[split]['question']) for split in data.keys() if 'question' in data[split])
        
        print(f"\n✓ Downloaded {total_questions:,} questions")
        print(f"✓ Splits: {', '.join(data.keys())}")
        print(f"✓ Saved to: {output_file}")
        
        return dataset
        
    except Exception as e:
        print(f"\n✗ Error downloading MedQA: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify HuggingFace datasets library is installed")
        print("3. Try: pip install --upgrade datasets")
        return None

def download_amqa():
    """Download AMQA from GitHub."""
    print("\n" + "=" * 60)
    print("Downloading AMQA from GitHub")
    print("=" * 60)
    
    import subprocess
    
    repo_url = "https://github.com/xy-showing/amqa.git"
    clone_path = project_root / 'data' / 'raw' / 'amqa'
    
    if clone_path.exists():
        print(f"\n✓ AMQA already exists at {clone_path}")
        print("  Skipping download...")
        return True
    
    try:
        print(f"\nCloning repository...")
        result = subprocess.run(
            ['git', 'clone', repo_url, str(clone_path)],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Cloned AMQA to {clone_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to clone AMQA")
        print(f"Error: {e.stderr}")
        print("\nManual download option:")
        print(f"1. Visit: {repo_url}")
        print(f"2. Download ZIP and extract to: {clone_path}")
        return False
    except FileNotFoundError:
        print("\n✗ Git not found on system")
        print("\nPlease install Git or download manually:")
        print(f"1. Visit: {repo_url}")
        print(f"2. Download ZIP and extract to: {clone_path}")
        return False

def verify_downloads():
    """Verify that downloads were successful."""
    print("\n" + "=" * 60)
    print("Verifying Downloads")
    print("=" * 60)
    
    medqa_file = project_root / 'data' / 'raw' / 'medqa_usmle_full.json'
    amqa_dir = project_root / 'data' / 'raw' / 'amqa'
    
    all_good = True
    
    # Check MedQA
    if medqa_file.exists():
        size_mb = medqa_file.stat().st_size / (1024 * 1024)
        print(f"\n✓ MedQA: Found ({size_mb:.1f} MB)")
        
        # Quick validation
        try:
            with open(medqa_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  Splits: {', '.join(data.keys())}")
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            all_good = False
    else:
        print(f"\n✗ MedQA: Not found at {medqa_file}")
        all_good = False
    
    # Check AMQA
    if amqa_dir.exists() and amqa_dir.is_dir():
        files = list(amqa_dir.glob('*'))
        print(f"\n✓ AMQA: Found ({len(files)} files/folders)")
    else:
        print(f"\n✗ AMQA: Not found at {amqa_dir}")
        all_good = False
    
    return all_good

def main():
    """Main execution function."""
    print("=" * 60)
    print("BanglaMedBias - Dataset Download Script")
    print("Stage 1: Data Collection")
    print("=" * 60)
    
    # Download MedQA
    medqa_dataset = download_medqa()
    
    # Download AMQA
    amqa_success = download_amqa()
    
    # Verify downloads
    if verify_downloads():
        print("\n" + "=" * 60)
        print("✓ All Downloads Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Explore the data:")
        print("   python scripts/filter/explore_data.py")
        print("\n2. Filter vignettes:")
        print("   python scripts/filter/filter_vignettes.py")
    else:
        print("\n" + "=" * 60)
        print("✗ Some downloads failed")
        print("=" * 60)
        print("\nPlease resolve errors above and try again.")

if __name__ == "__main__":
    main()
