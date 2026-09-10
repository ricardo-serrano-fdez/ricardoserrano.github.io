# Multi-Agent Knee MRI Diagnostic System: Architecture & Implementation Plan

## 1. Project Overview

The objective is to build a multi-agent system for automated knee injury diagnosis using MRI image data:
1. **Agent 1 (Vision-to-Report)**: Ingests DICOM (`.dcm`) MRI volume series and outputs structured/semi-structured radiological lesion observations and textual findings.
2. **Agent 2 (Diagnostic Interpreter)**: Ingests the lesion findings/report and deterministically maps them through a clinical decision tree to generate the final diagnostic classification.

```
 ┌──────────────────────┐         ┌───────────────────────────────┐         ┌───────────────────────────────┐
 │   Input MRI Series   │  ───►   │            Agent 1            │  ───►   │            Agent 2            │  ───►  Final Diagnosis
 │  (.dcm / 3D DICOM)   │         │ (MRI Vision-to-Report Model)  │         │ (Deterministic Tree/Reasoner) │        & Clinical Summary
 └──────────────────────┘         └───────────────────────────────┘         └───────────────────────────────┘
                                                  │                                         │
                                       Outputs structured findings               Maps findings along formal
                                       (ACL, Meniscus, Cartilage, etc.)          decision tree to diagnosis
```

---

## 2. Agent 1: MRI Vision-to-Report Model

### 2.1 Data Characteristics & Preprocessing
- **Modality**: DICOM (`.dcm`) multi-slice 2D/3D volumes.
- **Acquisitions**: Multiple MRI sequences/planes (e.g., Sagittal T1/T2/PD-FS, Coronal T1/T2/PD-FS, Axial).
- **Preprocessing Pipeline**:
  - DICOM parsing via `pydicom` / `SimpleITK`.
  - Slice thickness / voxel spacing normalization and volume resampling.
  - Hounsfield/Intensity normalization and contrast windowing.
  - 3D spatial alignment or slice selection.

### 2.2 Model Architecture Candidates
1. **Medical Vision-Language Model (VLM) Fine-Tuning**:
   - Models: RadVLM, BiomedCLIP, Med-PaLM, or LLaVA-Med.
   - Purpose: End-to-end report generation from MRI volume embeddings.
2. **3D CNN / 3D ViT Feature Extractor + Sequence Generator**:
   - Backbones: 3D ResNet-50, 3D DenseNet, MRNet architecture, Swin UNETR (MONAI).
   - Decoder: Transformer decoder generating radiology findings text.
3. **Multi-Task Structured Finding Predictor**:
   - Predicts discrete anatomical status (e.g., ACL: Intact/Partial Tear/Complete Tear; Meniscus: Normal/Tear; Cartilage: Grade 0–4) paired with templated narrative generation for 100% structured consistency.

---

## 3. Agent 2: Decision Tree / Diagnostic Interpreter

### 3.1 Core Requirements
- **Strict Logic Adherence**: Must follow a well-defined clinical decision tree without hallucination or ungrounded conclusions.
- **Traceability**: Every diagnostic label must provide explicit audit trails to the exact lesion findings in Agent 1's output.

### 3.2 Implementation Approaches
1. **Deterministic Rule Engine / Expert Graph (Recommended Baseline)**:
   - State-machine or directed acyclic graph (DAG) via Python (`networkx` or structured rule engines).
   - Guarantees 0% hallucination and full explainability.
2. **Constrained LLM Reasoner**:
   - Small language model (e.g., Llama-3-8B, Mistral-7B, BioMistral) utilizing structured constrained decoding (`Instructor`, `Outlines`, or JSON schema enforcement) following chain-of-thought rules.
3. **Interpretable Tree Classifiers**:
   - Decision Tree / RuleFit / LightGBM trained directly on tabular or tagged report features against diagnostic labels.

---

## 4. Phased Implementation Roadmap

- **Phase 1: Ingestion & Exploratory Data Analysis (EDA)**
  - Ingest sample `.dcm` files and inspect sequence dimensions, resolutions, and metadata.
  - Analyze report dataset and paired diagnoses to define the target schema.
- **Phase 2: Agent 1 Model Pipeline**
  - Implement DICOM data loaders and preprocessing transforms (`monai` / `pydicom` / `torchvision`).
  - Train/fine-tune the vision-to-report model on paired MRI-report samples.
- **Phase 3: Agent 2 Decision Tree Pipeline**
  - Formalize the clinical decision tree into executable code.
  - Validate Agent 2 on ground-truth reports to ensure 100% diagnostic accuracy against the decision tree.
- **Phase 4: Multi-Agent Orchestration & End-to-End Evaluation**
  - Build orchestrator pipeline linking Agent 1 output directly into Agent 2.
  - Evaluate end-to-end performance using clinical metrics (Sensitivity, Specificity, ROC-AUC, BLEU/ROUGE for reports).
