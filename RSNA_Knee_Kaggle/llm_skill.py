"""
LLM Reasoning Skill for Knee MRI Diagnostic Interpreter.
Provides multi-lingual understanding, structured section extraction,
and clinical reasoning for all 12 RSNA Knee target labels.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

SYSTEM_PROMPT = """You are an expert musculoskeletal radiologist and medical diagnostic agent.
Your task is to analyze raw knee MRI reports written in ANY language (English, Spanish, French, German, Dutch, Turkish, Bulgarian, Greek, etc.) and:
1. Translate and organize the findings into canonical standardized clinical sections.
2. Formulate concise, numbered clinical impressions deducted directly from the findings.
3. Classify exactly the 12 binary RSNA Knee diagnostic targets (0 = absent/normal, 1 = present/pathological) based on the report.

CRITICAL INSTRUCTIONS FOR 12 DIAGNOSTIC LABELS:
- ACL (0/1): 1 if ACL tear (complete/partial), rupture, avulsion, or high-grade sprain. 0 if intact/normal.
- MCL (0/1): 1 if MCL tear, sprain, or fiber disruption. 0 if intact/normal.
- Medial Meniscus (0/1): 1 if medial meniscus tear (radial, horizontal, root, complex, bucket-handle, maceration). 0 if intact or simple grade 1/2 degeneration without tear.
- Lateral Meniscus (0/1): 1 if lateral meniscus tear. 0 if intact or simple degeneration without tear.
- Medial OA (0/1): 1 if medial tibiofemoral osteoarthritis, severe medial chondrosis (Grade 3/4 / full-thickness loss), medial joint space narrowing, or medial osteophytes. 0 if normal or mild superficial chondrosis.
- Lateral OA (0/1): 1 if lateral tibiofemoral osteoarthritis, severe lateral chondrosis, or lateral osteophytes. 0 if normal.
- PF OA (0/1): 1 if patellofemoral osteoarthritis, patellar chondromalacia (Grade 2-4 / moderate-to-severe), or full-thickness patellar/trochlear cartilage loss. 0 if normal or grade 1.
- Effusion (0/1): 1 if joint effusion, hemarthrosis, or lipohemarthrosis is present. 0 if no effusion or trace physiologic fluid.
- Synovitis (0/1): 1 if synovitis, synovial thickening, synovial hypertrophy, or PVNS is mentioned. 0 if absent/normal.
- Baker's (0/1): 1 if Baker's cyst or popliteal cyst is present. 0 if absent or explicitly negative.
- Contusion (0/1): 1 if bone contusion, bone bruise, or post-traumatic marrow edema is present. 0 if normal marrow signal.
- Fracture (0/1): 1 if acute/subacute fracture, avulsion fracture, or tibial plateau fracture is present. 0 if no fracture.

Respond ONLY with valid JSON conforming to this exact schema:
{
  "findings": {
    "osseous_structures": "Detailed text describing bone marrow, contusion, fracture, osteophytes, or normal alignment",
    "joint_space": "Detailed text describing effusion, Baker's cyst, synovitis, bodies",
    "medial_meniscus": "Detailed text describing medial meniscus status",
    "medial_cartilage": "Detailed text describing medial compartment cartilage and OA changes",
    "lateral_meniscus": "Detailed text describing lateral meniscus status",
    "lateral_cartilage": "Detailed text describing lateral compartment cartilage and OA changes",
    "patellofemoral_cartilage": "Detailed text describing patellar and trochlear cartilage and OA changes",
    "acl": "Detailed text describing ACL status",
    "pcl": "Detailed text describing PCL status",
    "mcl": "Detailed text describing MCL status",
    "lcl_and_plc": "Detailed text describing LCL complex and posterolateral corner",
    "extensor_mechanism": "Detailed text describing quadriceps, patellar tendon, MPFL, tracking",
    "muscles_tendons": "Detailed text describing muscles and tendons",
    "soft_tissues": "Detailed text describing soft tissues, edema, neurovascular bundle"
  },
  "impressions": [
    "Numbered impression point 1",
    "Numbered impression point 2"
  ],
  "diagnoses": {
    "ACL": 0,
    "MCL": 0,
    "Medial Meniscus": 0,
    "Lateral Meniscus": 0,
    "Medial OA": 0,
    "Lateral OA": 0,
    "PF OA": 0,
    "Effusion": 0,
    "Synovitis": 0,
    "Baker's": 0,
    "Contusion": 0,
    "Fracture": 0
  },
  "reasoning": {
    "ACL": "Brief clinical justification",
    "MCL": "Brief clinical justification",
    "Medial Meniscus": "Brief clinical justification",
    "Lateral Meniscus": "Brief clinical justification",
    "Medial OA": "Brief clinical justification",
    "Lateral OA": "Brief clinical justification",
    "PF OA": "Brief clinical justification",
    "Effusion": "Brief clinical justification",
    "Synovitis": "Brief clinical justification",
    "Baker's": "Brief clinical justification",
    "Contusion": "Brief clinical justification",
    "Fracture": "Brief clinical justification"
  }
}
"""


def call_llm_api(prompt: str, system_prompt: str, model: str = "gpt-4o-mini", api_key: Optional[str] = None, base_url: Optional[str] = None) -> str:
    """Invokes OpenAI-compatible API endpoint via urllib."""
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"} if "gpt-" in model else None
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}" if key else ""
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content']


def generate_report_llm(
    raw_report: str,
    study_uid: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Skill: 'generate_report_llm'
    Ingests a raw report in any language, performs clinical reasoning,
    and returns canonical findings, impressions, and diagnoses.
    """
    user_prompt = f"StudyInstanceUID: {study_uid}\n\nRAW REPORT TO ANALYZE:\n```text\n{raw_report}\n```"

    try:
        response_text = call_llm_api(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            model=model,
            api_key=api_key,
            base_url=base_url
        )
        parsed = json.loads(response_text)
        return parsed
    except Exception as e:
        # Fallback structure if API call fails or is offline
        from decision_tree import KneeDecisionTree
        from report_structurer import extract_raw_sections, build_impressions_list
        
        eval_res = KneeDecisionTree.evaluate_all(raw_report)
        preds = eval_res['predictions']
        audit = eval_res['audit_trail']
        _, raw_imp = extract_raw_sections(raw_report)
        impressions = build_impressions_list(preds, raw_imp)

        return {
            "findings": {
                "osseous_structures": "Evaluated via fallback engine.",
                "joint_space": "Evaluated via fallback engine.",
                "medial_meniscus": "Evaluated via fallback engine.",
                "medial_cartilage": "Evaluated via fallback engine.",
                "lateral_meniscus": "Evaluated via fallback engine.",
                "lateral_cartilage": "Evaluated via fallback engine.",
                "patellofemoral_cartilage": "Evaluated via fallback engine.",
                "acl": "Evaluated via fallback engine.",
                "pcl": "Evaluated via fallback engine.",
                "mcl": "Evaluated via fallback engine.",
                "lcl_and_plc": "Evaluated via fallback engine.",
                "extensor_mechanism": "Evaluated via fallback engine.",
                "muscles_tendons": "Evaluated via fallback engine.",
                "soft_tissues": "Evaluated via fallback engine."
            },
            "impressions": impressions,
            "diagnoses": preds,
            "reasoning": audit,
            "error_note": f"LLM API call failed or offline ({str(e)}); used deterministic rules fallback."
        }
