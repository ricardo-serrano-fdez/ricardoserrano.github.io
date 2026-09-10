import json
import pandas as pd
from decision_tree import KneeDecisionTree

df = pd.read_csv('RSNA_Knee_Kaggle/train.csv')
labeled = df[df['ACL'].notnull()].copy()
target_cols = ['ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus', 'Medial OA', 'Lateral OA', 'PF OA', 'Effusion', 'Synovitis', "Baker's", 'Contusion', 'Fracture']

errors_by_col = {c: [] for c in target_cols}

for idx, row in labeled.iterrows():
    text = str(row['Report'])
    res = KneeDecisionTree.evaluate_all(text)
    preds = res['predictions']
    
    for c in target_cols:
        y_true = int(row[c])
        y_pred = preds[c]
        if y_true != y_pred:
            errors_by_col[c].append({
                'uid': row['StudyInstanceUID'],
                'true': y_true,
                'pred': y_pred,
                'audit': res['audit_trail'][c],
                'snippet': text[:400]
            })

for c in ['Medial OA', 'Lateral OA', 'PF OA', 'ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus']:
    print(f"\n=================== ERRORS FOR {c} (Total: {len(errors_by_col[c])}) ===================")
    for err in errors_by_col[c][:4]:
        print(f"UID: {err['uid']} | True: {err['true']} | Pred: {err['pred']}")
        print(f"Audit: {err['audit']}")
        print(f"Text snippet: {err['snippet']}")
        print("-" * 50)
