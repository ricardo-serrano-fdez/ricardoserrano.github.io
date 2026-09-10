"""
Report Structurer Module:
Standardizes multi-lingual Knee MRI raw reports into canonical FINDINGS and IMPRESSION format.
"""

import re
from typing import Dict, List, Tuple, Any

def extract_raw_sections(raw_text: str) -> Tuple[str, str]:
    text = str(raw_text).strip()
    markers = [
        r'(?:^|\n)\s*(?:IMPRESSION|CONCLUSION|CONCLUSIÓN|IMPRESIÓN|BESLUIT|SCHLUSSFOLGERUNG|SONUÇ|ЗАКЛЮЧЕНИЕ|ΣΥΜΠΕΡΑΣΜΑ)\s*[:：]?',
    ]
    for m in markers:
        match = re.search(m, text, re.IGNORECASE)
        if match:
            return text[:match.start()].strip(), text[match.end():].strip()
    return text, ""

def build_impressions_list(diagnoses: Dict[str, int], raw_imp: str) -> List[str]:
    impressions = []
    if diagnoses.get('ACL', 0) == 1:
        impressions.append("Anterior cruciate ligament (ACL) tear / injury.")
    if diagnoses.get('MCL', 0) == 1:
        impressions.append("Medial collateral ligament (MCL) sprain / tear.")
    if diagnoses.get('Medial Meniscus', 0) == 1 and diagnoses.get('Lateral Meniscus', 0) == 1:
        impressions.append("Bicompartmental meniscal tearing (medial and lateral).")
    elif diagnoses.get('Medial Meniscus', 0) == 1:
        impressions.append("Medial meniscus tear.")
    elif diagnoses.get('Lateral Meniscus', 0) == 1:
        impressions.append("Lateral meniscus tear.")
        
    oa = []
    if diagnoses.get('Medial OA', 0) == 1: oa.append("medial tibiofemoral")
    if diagnoses.get('Lateral OA', 0) == 1: oa.append("lateral tibiofemoral")
    if diagnoses.get('PF OA', 0) == 1: oa.append("patellofemoral")
    if len(oa) == 3:
        impressions.append("Tricompartmental osteoarthritis.")
    elif oa:
        impressions.append(f"Osteoarthritis involving {' and '.join(oa)} compartment(s).")
        
    if diagnoses.get('Fracture', 0) == 1:
        impressions.append("Acute osseous fracture.")
    if diagnoses.get('Contusion', 0) == 1:
        impressions.append("Bone contusion / post-traumatic marrow edema.")
    if diagnoses.get('Effusion', 0) == 1:
        impressions.append("Joint effusion.")
    if diagnoses.get('Synovitis', 0) == 1:
        impressions.append("Synovitis / synovial thickening.")
    if diagnoses.get("Baker's", 0) == 1:
        impressions.append("Popliteal (Baker's) cyst.")
        
    if not impressions:
        impressions.append(raw_imp if raw_imp else "No acute osseous, ligamentous, or meniscal abnormality.")
    return impressions

def generate_structured_report(study_uid: str, raw_text: str, diagnoses: Dict[str, int]) -> str:
    raw_findings, raw_imp = extract_raw_sections(raw_text)
    impressions = build_impressions_list(diagnoses, raw_imp)
    imp_text = "\n".join([f"{i+1}.\t{item}" for i, item in enumerate(impressions)])
    
    osseous = "Bone contusion / post-traumatic marrow edema present." if diagnoses.get('Contusion') else "No acute fracture or bone bruise."
    fracture_txt = "Acute osseous fracture identified." if diagnoses.get('Fracture') else "Background marrow signal is normal without aggressive lesions."
    effusion_txt = "Joint effusion present." if diagnoses.get('Effusion') else "No joint effusion."
    baker_txt = "Baker's cyst identified." if diagnoses.get("Baker's") else "No Baker's cyst."
    synovitis_txt = "Synovial proliferation / synovitis present." if diagnoses.get('Synovitis') else "Normal synovial membrane."
    
    med_men_txt = "Tear present." if diagnoses.get('Medial Meniscus') else "Normal in morphology and signal without tear."
    med_oa_txt = "Degenerative changes / cartilage loss consistent with medial OA." if diagnoses.get('Medial OA') else "Preserved articular cartilage."
    lat_men_txt = "Tear present." if diagnoses.get('Lateral Meniscus') else "Normal in morphology and signal without tear."
    lat_oa_txt = "Degenerative changes / cartilage loss consistent with lateral OA." if diagnoses.get('Lateral OA') else "Preserved articular cartilage."
    pf_oa_txt = "High-grade cartilage loss / chondromalacia / patellofemoral OA." if diagnoses.get('PF OA') else "Preserved patellofemoral articular cartilage."
    acl_txt = "Tear / sprain / significant disruption identified." if diagnoses.get('ACL') else "Normal with both bundles intact."
    mcl_txt = "Sprain / tear identified." if diagnoses.get('MCL') else "Normal."

    report = f"""# Knee MRI Diagnostic Report
**StudyInstanceUID**: `{study_uid}`

## FINDINGS:

### OSSEOUS STRUCTURES:
Alignment is anatomical. {osseous} {fracture_txt}

### JOINT SPACE:
{effusion_txt} {baker_txt} {synovitis_txt}

### MEDIAL COMPARTMENT:
- **Medial meniscus**: {med_men_txt}
- **Medial compartment cartilage**: {med_oa_txt}

### LATERAL COMPARTMENT:
- **Lateral meniscus**: {lat_men_txt}
- **Lateral compartment cartilage**: {lat_oa_txt}

### PATELLOFEMORAL COMPARTMENT:
- **Patellofemoral compartment cartilage**: {pf_oa_txt}

### CRUCIATE LIGAMENTS:
- **Anterior cruciate ligament (ACL)**: {acl_txt}
- **Posterior cruciate ligament (PCL)**: Normal.

### COLLATERAL LIGAMENTS & POSTEROLATERAL CORNER:
- **Medial collateral ligament (MCL)**: {mcl_txt}
- **Lateral collateral ligament (LCL) complex**: Normal.
- **Posterolateral corner structures**: Normal.

### EXTENSOR MECHANISM:
- **Distal quadriceps tendon**: Normal without tendinosis or tear.
- **Patella tendon**: Normal without tendinosis or tear.
- **Medial patellofemoral ligament (MPFL) and patellar retinacula**: Normal.
- **Patellofemoral tracking**: Normal.

### MUSCLES/TENDONS:
No acute muscle strain or muscle atrophy. Visualized tendons intact.

### SOFT TISSUES:
Normal surrounding soft tissues and neurovascular bundles.

---

## IMPRESSION:
{imp_text}

---
### Source Raw Report:
```text
{raw_text.strip()}
```
"""
    return report


def generate_structured_report_from_llm(study_uid: str, raw_text: str, llm_output: Dict[str, Any]) -> str:
    findings = llm_output.get("findings", {})
    impressions = llm_output.get("impressions", [])
    if isinstance(impressions, list):
        imp_text = "\n".join([f"{i+1}.\t{item}" for i, item in enumerate(impressions)])
    else:
        imp_text = str(impressions)

    f_osseous = findings.get("osseous_structures", "Alignment is anatomical. No acute fracture or bone bruise.")
    f_joint = findings.get("joint_space", "No joint effusion. No Baker's cyst.")
    f_med_men = findings.get("medial_meniscus", "Normal in morphology and signal without tear.")
    f_med_cart = findings.get("medial_cartilage", "Preserved articular cartilage.")
    f_lat_men = findings.get("lateral_meniscus", "Normal in morphology and signal without tear.")
    f_lat_cart = findings.get("lateral_cartilage", "Preserved articular cartilage.")
    f_pf_cart = findings.get("patellofemoral_cartilage", "Preserved patellofemoral articular cartilage.")
    f_acl = findings.get("acl", "Normal with both bundles intact.")
    f_pcl = findings.get("pcl", "Normal.")
    f_mcl = findings.get("mcl", "Normal.")
    f_lcl = findings.get("lcl_and_plc", "Normal.")
    f_ext = findings.get("extensor_mechanism", "Distal quadriceps and patellar tendons intact without tear. Normal patellofemoral tracking.")
    f_musc = findings.get("muscles_tendons", "No acute muscle strain or muscle atrophy. Visualized tendons intact.")
    f_soft = findings.get("soft_tissues", "Normal surrounding soft tissues and neurovascular bundles.")

    report = f"""# Knee MRI Diagnostic Report
**StudyInstanceUID**: `{study_uid}`

## FINDINGS:

### OSSEOUS STRUCTURES:
{f_osseous}

### JOINT SPACE:
{f_joint}

### MEDIAL COMPARTMENT:
- **Medial meniscus**: {f_med_men}
- **Medial compartment cartilage**: {f_med_cart}

### LATERAL COMPARTMENT:
- **Lateral meniscus**: {f_lat_men}
- **Lateral compartment cartilage**: {f_lat_cart}

### PATELLOFEMORAL COMPARTMENT:
- **Patellofemoral compartment cartilage**: {f_pf_cart}

### CRUCIATE LIGAMENTS:
- **Anterior cruciate ligament (ACL)**: {f_acl}
- **Posterior cruciate ligament (PCL)**: {f_pcl}

### COLLATERAL LIGAMENTS & POSTEROLATERAL CORNER:
- **Medial collateral ligament (MCL)**: {f_mcl}
- **Lateral collateral ligament (LCL) complex**: {f_lcl}
- **Posterolateral corner structures**: Normal.

### EXTENSOR MECHANISM:
{f_ext}

### MUSCLES/TENDONS:
{f_musc}

### SOFT TISSUES:
{f_soft}

---

## IMPRESSION:
{imp_text}

---
### Source Raw Report:
```text
{raw_text.strip()}
```
"""
    return report

    return report
