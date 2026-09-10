import pandas as pd
from decision_tree import KneeDecisionTree

df = pd.read_csv('RSNA_Knee_Kaggle/train.csv')
labeled = df[df['ACL'].notnull()].copy()
target_cols = ['ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus', 'Medial OA', 'Lateral OA', 'PF OA', 'Effusion', 'Synovitis', "Baker's", 'Contusion', 'Fracture']

correct = {c: 0 for c in target_cols}
tp = {c: 0 for c in target_cols}
fp = {c: 0 for c in target_cols}
fn = {c: 0 for c in target_cols}
tn = {c: 0 for c in target_cols}

total = len(labeled)

for idx, row in labeled.iterrows():
    text = str(row['Report'])
    res = KneeDecisionTree.evaluate_all(text)
    preds = res['predictions']
    
    for c in target_cols:
        y_true = int(row[c])
        y_pred = preds[c]
        if y_true == y_pred:
            correct[c] += 1
            if y_true == 1:
                tp[c] += 1
            else:
                tn[c] += 1
        else:
            if y_pred == 1 and y_true == 0:
                fp[c] += 1
            else:
                fn[c] += 1

print(f"--- Benchmark Results on N={total} Ground Truth Rows ---")
print(f"{'Target':<18} | {'Accuracy':<8} | {'Precision':<10} | {'Recall':<8} | {'F1-Score':<8} | TP/FP/FN/TN")
print("-" * 75)

for c in target_cols:
    acc = correct[c] / total
    prec = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0.0
    rec = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    print(f"{c:<18} | {acc*100:6.1f}%  | {prec*100:8.1f}%  | {rec*100:6.1f}% | {f1*100:6.1f}%  | {tp[c]}/{fp[c]}/{fn[c]}/{tn[c]}")
