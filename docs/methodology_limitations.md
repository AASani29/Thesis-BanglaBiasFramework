# Methodology Limitations

## Study Design Limitations

### 1. Multiple-Choice Question Format Constraints

**Limitation:** The use of MCQ-based clinical vignettes, while enabling quantifiable bias measurement, constrains the scope of detectable bias to diagnostic accuracy rather than comprehensive clinical decision-making.

**Implications:**

- The binary correct/incorrect metric does not capture the nuanced ways bias may manifest in clinical reasoning, such as differences in confidence levels, diagnostic certainty, or reasoning pathways.
- Models may arrive at the correct diagnosis through biased reasoning that remains undetected. For example, a model might rely on socioeconomic stereotypes about healthcare access or lifestyle factors while still selecting the correct answer.
- The forced-choice format eliminates the opportunity to observe bias in differential diagnosis generation, treatment prioritization, or patient communication strategies.

**Mitigation:** We acknowledge that this study measures diagnostic accuracy bias as a specific dimension of algorithmic bias in medical AI, not comprehensive clinical bias. Future research should incorporate open-ended response formats to capture reasoning patterns and decision-making processes.

---

### 2. Limited Bias Dimensionality

**Limitation:** The study primarily focuses on demographic bias (socioeconomic status, geographic location, gender) in diagnostic accuracy, excluding other critical dimensions of healthcare bias.

**Unmeasured Bias Types:**

- **Treatment bias:** Differential recommendations for interventions, medications, or referrals based on patient demographics
- **Resource allocation bias:** Variations in suggesting expensive tests, specialist consultations, or intensive interventions
- **Communication bias:** Differences in explanation complexity, empathy, or patient education approaches
- **Cultural competency:** Appropriateness of recommendations considering Bangladesh-specific cultural, religious, or social contexts
- **Follow-up care bias:** Variations in suggested monitoring frequency or preventive care recommendations

**Justification:** Diagnostic accuracy represents the foundational step in clinical care and is essential for patient safety. Establishing the presence or absence of diagnostic bias is a necessary first step before examining downstream treatment and communication biases.

---

### 3. Translation-Related Confounds

**Limitation:** The study involves translation from English (MedQA-USMLE) to Bangla, introducing potential confounds between translation quality effects and demographic bias effects.

**Specific Concerns:**

- Medical terminology standardization: Bangla medical terms vary in formality and regional usage, potentially affecting model comprehension differentially across demographic variants
- Semantic equivalence: Some English medical concepts may not have direct Bangla equivalents, requiring paraphrasing that could alter clinical meaning
- Cultural framing: Translation involves more than linguistic conversion; cultural adaptation of scenarios may inadvertently introduce or mask bias signals
- Language model training data: Most large language models have significantly more English medical text in training data compared to Bangla, potentially affecting baseline performance

**Mitigation Strategies:**

- Dual-LLM validation pipeline (GPT-4o translation, Claude 3.5 validation) to ensure translation quality
- Medical expert review by three Bangladeshi physicians to validate clinical accuracy and cultural appropriateness
- Separate analysis of model performance on English vs. Bangla versions to quantify translation effects
- Future work: Test with Bangla-optimized models (e.g., BanglaBERT, BanglaT5) to isolate language-specific effects

---

### 4. Confidence Score Availability

**Limitation:** Depending on model API access, capturing prediction confidence scores may not be possible for all tested models, limiting bias detection sensitivity.

**Impact:**

- Binary accuracy (correct/incorrect) is a coarse-grained metric that may miss subtle bias manifestations
- Confidence scores can reveal bias even when accuracy is equal (e.g., consistently lower confidence for rural/poor variants despite correct answers)
- Some models (especially proprietary or black-box systems) may not expose probability distributions over answer choices
- Confidence calibration differs across models, making cross-model comparisons challenging

**Approach:**

- For API-accessible models (GPT-4, Claude, Gemini), we will capture logit probabilities or confidence scores where available
- For models without confidence exposure, we acknowledge this as a limitation and focus on accuracy-based metrics
- Analyze confidence patterns as secondary outcome where data permits

---

### 5. Sample Size and Statistical Power

**Limitation:** 500 base vignettes expanded to 3,000 demographic variants (500 × 6 variants) may have limited statistical power for detecting small effect sizes in specific medical categories or demographic intersections.

**Considerations:**

- Medical category representation: Some categories have limited samples (e.g., psychiatric: 1, pharmacology: 2, dermatology: 7)
- Intersectional analysis: Examining interactions between socioeconomic status, geography, and gender requires sufficient samples in each cell
- Effect size detection: The study is powered to detect moderate-to-large bias effects but may miss subtle biases
- Multiple comparison correction: Testing across 14 medical categories, 6 demographic variants, and multiple models requires stringent statistical corrections, reducing sensitivity

**Power Analysis:** Based on standard effect size conventions for medical research:

- Minimum detectable accuracy difference: ≥5% between demographic groups (Cohen's h ≈ 0.25)
- Statistical significance threshold: α = 0.01 (Bonferroni-corrected for multiple comparisons)
- Estimated power: 80% for moderate effects, 95% for large effects

---

### 6. Temporal Validity

**Limitation:** Dataset derived from MedQA-USMLE (based on US medical licensing exams) reflects Western medical education paradigms and may have temporal limitations.

**Concerns:**

- Clinical practice evolution: Medical knowledge and guidelines change; dataset may not reflect current best practices in Bangladesh (2026)
- Epidemiological context: Disease burden distributions targeted in sampling may shift over time
- Model training data cutoff: Large language models have knowledge cutoffs; newer models may have different biases than older models tested in this study
- Healthcare system changes: Bangladesh healthcare infrastructure and access patterns are dynamic

**Validity Enhancement:**

- Medical expert reviewers assess current clinical relevance of vignettes
- Target disease distribution based on recent Bangladesh epidemiological data (DGHS 2024 reports)
- Document model versions and training cutoffs for reproducibility
- Acknowledge that findings represent a snapshot of bias patterns as of 2026

---

### 7. Generalizability Constraints

**Limitation:** Findings may not generalize beyond the specific context of this study.

**Scope Boundaries:**

- **Language specificity:** Results apply to Bangla-language medical AI; bias patterns may differ in other languages
- **Medical domain:** Focus on internal medicine/primary care vignettes; does not cover surgical, pediatric subspecialties, or emergency medicine comprehensively
- **Demographic dimensions:** Study focuses on Bangladesh-relevant socioeconomic and geographic factors; does not examine ethnicity, religion, disability, or other bias dimensions
- **Model selection:** Testing limited to specific large language models available in 2026; newer architectures may exhibit different bias patterns
- **Question format:** MCQ-based evaluation; real clinical interactions involve natural language queries and conversational context

**Transferability:** While specific bias magnitudes may not transfer, the methodology provides a framework applicable to other languages, medical domains, and demographic contexts.

---

### 8. Ground Truth Assumptions

**Limitation:** The study assumes the original MedQA-USMLE answer key represents unbiased medical ground truth.

**Considerations:**

- Source dataset (US medical licensing exams) reflects Western medical education and may embed cultural or resource availability assumptions
- "Correct" answers may be context-dependent (e.g., resource-limited settings may require different diagnostic approaches)
- Expert consensus on diagnoses may vary; some vignettes may have debatable answers
- Demographic neutralization assumes certain interventions apply equally across contexts (may not always hold)

**Validation:** Medical expert reviewers explicitly assess whether original diagnoses remain appropriate in Bangladesh context and can flag vignettes requiring answer adjustment.

---

## Strengths Despite Limitations

While acknowledging these constraints, the methodology offers several advantages:

1. **Standardization:** MCQ format enables reproducible, quantitative bias measurement across models
2. **Controlled comparison:** Demographic variants differ only in specified attributes, isolating bias sources
3. **Clinical realism:** Vignettes derived from actual medical licensing exams represent realistic clinical scenarios
4. **Scale:** 3,000 total test cases provide substantial data for statistical analysis
5. **Cultural grounding:** Translation and expert review ensure Bangladesh-specific relevance
6. **Methodological transparency:** Open documentation of filtering, categorization, and validation procedures

---

## Recommendations for Future Research

To address identified limitations, future studies should:

1. **Incorporate open-ended questions** to capture reasoning patterns and detect stereotyping in clinical explanations
2. **Expand bias dimensions** to treatment recommendations, resource allocation, and patient communication
3. **Develop Bangla-native medical datasets** to eliminate translation confounds
4. **Test across medical specialties** including surgery, pediatrics, psychiatry, and emergency medicine
5. **Examine intersectional bias** with larger samples enabling robust subgroup analysis
6. **Longitudinal assessment** to track how bias patterns evolve with model updates and training data changes
7. **Real-world validation** comparing bias patterns in synthetic vignettes vs. actual clinical deployment
8. **Confidence-based metrics** as primary outcome to capture nuanced bias manifestations

---

## Conclusion

This study employs a rigorous, quantifiable methodology for detecting diagnostic accuracy bias in medical AI systems for Bangladesh contexts. While MCQ-based evaluation has inherent limitations in capturing the full spectrum of clinical bias, it provides a necessary foundation for establishing whether demographic factors influence AI diagnostic performance. The acknowledged limitations should be considered when interpreting findings and designing interventions to mitigate identified biases.
