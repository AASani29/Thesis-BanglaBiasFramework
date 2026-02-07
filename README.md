# BanglaMedBias - Part 1: Dataset Preparation

**Project:** Creating the first comprehensive Bangla medical bias evaluation dataset  
**Stage:** Part 1 - Dataset Selection & Filtering (Before Translation)  
**Target:** 500 high-quality clinical vignettes from MedQA-USMLE

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Usage Guide](#usage-guide)
5. [What You Need to Provide](#what-you-need-to-provide)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## 🎯 Project Overview

This is **Part 1** of the BanglaMedBias project, which focuses on:

✅ Setting up the project structure  
✅ Downloading source datasets (MedQA-USMLE & AMQA)  
✅ Exploring and understanding the data  
✅ Filtering clinical vignettes based on quality criteria  
✅ Selecting 500 vignettes using stratified sampling  
✅ Quality validation before translation

**What This Part Does NOT Include:**

- Translation (Part 2)
- Expert validation (Part 3)
- Bias testing (Part 4)

---

## 📁 Project Structure

```
Implementation Part 1/
├── data/
│   ├── raw/                    # Downloaded datasets (not in git)
│   ├── filtered/               # Filtered vignettes
│   ├── translated/             # (Future: translations)
│   ├── validated/              # (Future: expert validation)
│   └── final/                  # (Future: final dataset)
│
├── scripts/
│   ├── download/
│   │   └── download_medqa.py   # Download MedQA & AMQA
│   ├── filter/
│   │   ├── explore_data.py     # Explore dataset structure
│   │   ├── filter_vignettes.py # Filter & select 500 vignettes
│   │   └── quality_check.py    # Quality validation
│   ├── translate/              # (Future: translation scripts)
│   ├── validate/               # (Future: validation scripts)
│   └── test/                   # (Future: bias testing)
│
├── outputs/
│   ├── logs/                   # Execution logs
│   ├── reports/                # Quality reports & statistics
│   ├── metrics/                # (Future: bias metrics)
│   └── figures/                # (Future: visualizations)
│
├── validation/                 # (Future: annotation files)
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── .env.example                # API key template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🔧 Installation

### Prerequisites

- **Python:** 3.10 or higher
- **Git:** For version control and cloning AMQA
- **Internet:** For downloading datasets

### Step 1: Clone or Navigate to Project

```powershell
cd "c:\Users\bashi\OneDrive\Desktop\Thesis\Bias Framework\Implementation Part 1"
```

### Step 2: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**If you're on a system-managed Python:**

```powershell
pip install -r requirements.txt --break-system-packages
```

### Step 3: Verify Installation

```powershell
python -c "import pandas; import datasets; print('✓ All dependencies installed')"
```

---

## 🚀 Usage Guide

### Stage 1.1: Download Datasets

**Script:** `scripts/download/download_medqa.py`

```powershell
python scripts/download/download_medqa.py
```

**What it does:**

- Downloads MedQA-USMLE dataset from HuggingFace (~12,700 questions)
- Clones AMQA repository from GitHub
- Saves data to `data/raw/`

**Expected output:**

```
============================================================
MedQA & AMQA Dataset Download
============================================================
✓ Downloaded 12,723 questions
✓ Saved to: data/raw/medqa_usmle_full.json
✓ Cloned AMQA to data/raw/amqa
✓ All Downloads Complete!
```

**Time:** 2-5 minutes (depending on internet speed)

---

### Stage 1.2: Explore Dataset

**Script:** `scripts/filter/explore_data.py`

```powershell
python scripts/filter/explore_data.py
```

**What it does:**

- Analyzes dataset structure and fields
- Calculates question length statistics
- Identifies clinical vignettes
- Analyzes demographic mentions (age, gender)
- Categorizes questions by medical topic
- Generates exploration report

**Expected output:**

```
============================================================
DATASET STRUCTURE ANALYSIS
============================================================
Total questions: 12,723
Fields available: question, options, answer, answer_idx, ...

Question Length Statistics:
  Average: 487 characters
  Clinical Vignettes: ~8,456 (66.5%)

✓ Exploration report saved to: outputs/reports/stage1_exploration_summary.txt
```

**Time:** 1-2 minutes

---

### Stage 1.3: Filter & Select Vignettes

**Script:** `scripts/filter/filter_vignettes.py`

```powershell
python scripts/filter/filter_vignettes.py
```

**What it does:**

- Applies filtering criteria:
  1. Must be clinical vignette (patient presentation)
  2. Must be demographically neutral (no gender-specific conditions)
  3. Must have exactly 4 answer options
  4. Must be reasonable length (150-2000 characters)
- Categorizes by medical domain
- Performs stratified sampling to select 500 vignettes
- Saves filtered and selected datasets

**Filtering criteria details:**

| Filter              | Description                                   | Example                              |
| ------------------- | --------------------------------------------- | ------------------------------------ |
| Clinical Vignette   | Contains patient, age, presentation, symptoms | "A 45-year-old man presents with..." |
| Demographic Neutral | No pregnancy, gender-specific organs          | ✗ "Pregnant woman..."                |
| 4 Options           | Exactly 4 multiple-choice answers             | A, B, C, D                           |
| Length              | 150-2000 characters                           | Not too short/long                   |

**Target distribution (Bangladesh disease burden):**

- Infectious diseases: 30% (150)
- Diabetes: 20% (100)
- Cardiovascular: 20% (100)
- Respiratory: 15% (75)
- Other conditions: 15% (75)

**Expected output:**

```
============================================================
FILTERING STATISTICS
============================================================
Total questions: 12,723
  Clinical vignettes:     8,456 (66.5%)
  Demographic neutral:    6,234 (49.0%)
  Has 4 options:          5,892 (46.3%)
  Reasonable length:      4,127 (32.4%)

✓ Final filtered:         2,156 (16.9%)

============================================================
STRATIFIED SAMPLING
============================================================
✓ Selected 500 vignettes

Final category breakdown:
  infectious:         150 (30.0%)
  diabetes:           100 (20.0%)
  cardiovascular:     100 (20.0%)
  respiratory:         75 (15.0%)
  gastrointestinal:    40 ( 8.0%)
  neurological:        20 ( 4.0%)
  renal:              15 ( 3.0%)
```

**Output files:**

- `data/filtered/medqa_filtered_all.json` - All filtered vignettes (~2,156)
- `data/filtered/medqa_selected_500.json` - Selected 500 vignettes
- `outputs/reports/stage1_filtering_stats.json` - Statistics

**Time:** 2-3 minutes

---

### Stage 1.4: Quality Check

**Script:** `scripts/filter/quality_check.py`

```powershell
python scripts/filter/quality_check.py
```

**What it does:**

- Validates completeness (all required fields present)
- Checks length distribution
- Validates clinical vignette structure
- Verifies category distribution
- Checks for diversity (age groups, no duplicates)
- Ensures ID uniqueness
- Generates quality report

**Expected output:**

```
============================================================
QUALITY CHECK REPORT
============================================================

✓ Completeness:           PASS ✓
✓ Length Distribution:    PASS ✓
✓ Readability:            PASS ✓
✓ Category Distribution:  PASS ✓
✓ Diversity:              PASS ✓
✓ ID Uniqueness:          PASS ✓

Overall: PASS ✓

✓✓✓ ALL CHECKS PASSED ✓✓✓
```

**Output:**

- `outputs/reports/stage1_quality_check.txt` - Detailed quality report

**Time:** <1 minute

---

## 📦 What You Need to Provide

### Required:

1. **Python 3.10+** installed
2. **Internet connection** for downloading datasets
3. **~500 MB disk space** for datasets

### NOT Required at This Stage:

- ❌ API keys (OpenAI, Anthropic) - needed for Part 2 (translation)
- ❌ Medical experts - needed for Part 3 (validation)
- ❌ LLM access - needed for Part 4 (bias testing)

### To Continue to Part 2 (Translation):

You will need:

- OpenAI API key (GPT-4o) - ~$5 for 500 translations
- Anthropic API key (Claude 3.5) - ~$3 for validation
- Create `.env` file from `.env.example` and add keys

---

## 🔍 Troubleshooting

### Issue: "datasets library not installed"

```powershell
pip install datasets --upgrade
```

### Issue: "Git not found" (for AMQA download)

- **Option 1:** Install Git from https://git-scm.com/
- **Option 2:** Manually download AMQA:
  1. Visit: https://github.com/xy-showing/amqa
  2. Download ZIP
  3. Extract to `data/raw/amqa/`

### Issue: "Only X vignettes after filtering"

- This is normal if dataset structure differs
- Check `outputs/reports/stage1_filtering_stats.json` for details
- You may need to adjust filtering criteria in `filter_vignettes.py`

### Issue: "HuggingFace download slow"

- Large dataset (~100 MB)
- Wait for download to complete
- Or download manually and place in `data/raw/`

### Issue: "Permission denied" on Windows

```powershell
# Run PowerShell as Administrator
pip install -r requirements.txt
```

---

## 📊 Expected Outputs After Part 1

After completing all scripts, you should have:

### Files:

```
data/filtered/
├── medqa_filtered_all.json      # ~2,156 filtered vignettes
└── medqa_selected_500.json      # 500 selected vignettes ✓

outputs/reports/
├── stage1_exploration_summary.txt
├── stage1_filtering_stats.json
└── stage1_quality_check.txt
```

### Key Metrics:

- ✅ **500 vignettes** selected and validated
- ✅ **Stratified by disease category** (infectious 30%, diabetes 20%, etc.)
- ✅ **All clinical vignettes** (patient presentations)
- ✅ **Demographically neutral** (adaptable for bias testing)
- ✅ **Quality validated** (completeness, length, structure)

---

## 🎯 Next Steps

### Part 2: Translation (Coming Next)

Once Part 1 is complete, you'll proceed to:

1. **Dual-LLM Translation Pipeline**
   - GPT-4o translates English → Bangla
   - Claude 3.5 validates translations
   - Cost: ~$8 total

2. **Expert Validation**
   - 3 Bangladeshi doctors review
   - Annotate quality, accuracy, context

3. **Bangladesh Context Adaptation**
   - Adapt demographics (urban/rural, wealth)
   - Create 6 variants per vignette

### To Prepare for Part 2:

1. Get OpenAI API key: https://platform.openai.com/api-keys
2. Get Anthropic API key: https://console.anthropic.com/
3. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your keys
   ```

---

## 📈 Project Timeline

| Stage                 | Status     | Duration   |
| --------------------- | ---------- | ---------- |
| **Part 1: Selection** | ✅ READY   | 1-2 days   |
| Part 2: Translation   | 🔜 Next    | 3-4 days   |
| Part 3: Validation    | ⏳ Pending | 2-3 weeks  |
| Part 4: Adaptation    | ⏳ Pending | 1 week     |
| Part 5: Testing       | ⏳ Pending | 2-3 weeks  |
| Part 6: Publication   | ⏳ Pending | 8-10 weeks |

---

## 🤝 Support

If you encounter issues:

1. **Check troubleshooting section above**
2. **Review error messages carefully**
3. **Check file paths** (especially on Windows with spaces)
4. **Verify Python version:** `python --version` (should be 3.10+)
5. **Check internet connection** for downloads

---

## 📝 Notes

- All scripts use **relative paths** from project root
- **Random seed** is set (42) for reproducibility
- **Data files** in `data/raw/` are gitignored (too large)
- **Output reports** help track progress and quality
- **Part 1 is standalone** - no API keys needed yet

---

## ✅ Checklist

Before moving to Part 2:

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] MedQA dataset downloaded (~12,723 questions)
- [ ] AMQA repository cloned
- [ ] Dataset explored (exploration report generated)
- [ ] Vignettes filtered (~2,156 candidates)
- [ ] 500 vignettes selected (stratified sampling)
- [ ] Quality check passed (all checks ✓)
- [ ] Output files exist in `data/filtered/`

**If all checks pass, you're ready for Part 2: Translation!**

---

**Last Updated:** February 2026  
**Version:** 1.0  
**Stage:** Part 1 - Dataset Preparation
