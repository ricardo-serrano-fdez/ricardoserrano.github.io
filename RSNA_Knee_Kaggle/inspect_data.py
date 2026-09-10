import pandas as pd
import json

df = pd.read_csv('RSNA_Knee_Kaggle/train.csv')
labeled = df[df['ACL'].notnull()]
print(f"Total rows: {len(df)}")
print(f"Total labeled rows: {len(labeled)}")

target_cols = ['ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus', 'Medial OA', 'Lateral OA', 'PF OA', 'Effusion', 'Synovitis', "Baker's", 'Contusion', 'Fracture']

samples = []
for idx, row in labeled.iterrows():
    sample = {
        'idx': idx,
        'StudyInstanceUID': row['StudyInstanceUID'],
        'Report': row['Report'],
        'labels': {c: int(row[c]) for c in target_cols}
    }
    samples.append(sample)

with open('RSNA_Knee_Kaggle/labeled_samples.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, indent=2, ensure_ascii=False)

print("Saved labeled samples to RSNA_Knee_Kaggle/labeled_samples.json")
