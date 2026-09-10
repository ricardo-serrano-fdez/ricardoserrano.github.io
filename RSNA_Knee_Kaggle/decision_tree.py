"""
Deterministic Clinical Decision Tree Engine for Knee MRI Diagnosis.
Evaluates the 12 target binary categories with negation handling and audit trails.
"""

import os
import json
import re
from typing import Dict, Any, Tuple

# Load rules from JSON
RULES_FILE = os.path.join(os.path.dirname(__file__), 'rules_definition.json')
with open(RULES_FILE, 'r', encoding='utf-8') as f:
    RULES = json.load(f)

NEG_TERMS = [
    r'\bno\b', r'\bnot\b', r'\bwithout\b', r'\babsence of\b', r'\bintact\b', r'\bnormal\b',
    r'\bpreserved\b', r'\bunremarkable\b', r'\bnegative\b', r'\bsin\b', r'\bno hay\b',
    r'\bconservad[ao]s?\b', r'\bnormales?\b', r'\bintact[ao]s?\b', r'\baucun\b', r'\baucune\b',
    r'\bsans\b', r'\bpas de\b', r'\bkein\b', r'\bkeine\b', r'\bkeinen\b', r'\bohne\b',
    r'\bintakt\b', r'\bunauffällig\b', r'\bregelrecht\b', r'\bgeen\b', r'\bzonder\b',
    r'\byoktur\b', r'\byok\b', r'\bnormaldir\b', r'\bняма\b', r'\bχωρίς\b',
]

def is_negated_context(context: str, match_str: str) -> bool:
    for neg in NEG_TERMS:
        m = re.search(neg, context)
        if m:
            after_neg = context[m.end():]
            if match_str.lower() in after_neg.lower() or any(w in after_neg for w in ['tear', 'rotura', 'rupture', 'scheur', 'riss', 'fracture', 'effusion', 'cyst', 'bruise']):
                if not re.search(r'\b(but|except|sin embargo|pero|mais|aber|maar|fakat)\b', after_neg):
                    return True
    return False

def check_match(text: str, patterns: list) -> Tuple[int, str]:
    lower = text.lower()
    for pat in patterns:
        for m in re.finditer(pat, lower):
            match_str = m.group(0)
            context = lower[max(0, m.start() - 40):min(len(lower), m.end() + 40)]
            if not is_negated_context(context, match_str):
                return 1, match_str
    return 0, ""

class KneeDecisionTree:
    @classmethod
    def evaluate_target(cls, target_name: str, text: str) -> Tuple[int, str]:
        pats = RULES.get(target_name, [])
        hit, match = check_match(text, pats)
        if hit:
            return 1, f"Positive: matched '{match}'"
        return 0, f"Negative / intact for {target_name}"

    @classmethod
    def evaluate_all(cls, text: str) -> Dict[str, Any]:
        targets = [
            'ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus',
            'Medial OA', 'Lateral OA', 'PF OA', 'Effusion',
            'Synovitis', "Baker's", 'Contusion', 'Fracture'
        ]
        predictions = {}
        audit_trail = {}
        for target in targets:
            pred, reason = cls.evaluate_target(target, text)
            predictions[target] = pred
            audit_trail[target] = reason
        return {'predictions': predictions, 'audit_trail': audit_trail}

