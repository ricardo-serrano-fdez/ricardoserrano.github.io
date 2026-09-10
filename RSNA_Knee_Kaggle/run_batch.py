import sys
import pandas as pd
from interpreter_agent import DiagnosticInterpreterAgent

def main():
    csv_path = 'RSNA_Knee_Kaggle/train.csv'
    agent = DiagnosticInterpreterAgent()
    df = pd.read_csv(csv_path)
    
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(df)
    subset = df.head(limit)
    print(f"Running agent on {len(subset)} studies...")
    
    results = []
    for idx, row in subset.iterrows():
        uid = str(row['StudyInstanceUID'])
        report = str(row['Report'])
        gt = None
        if pd.notnull(row.get('ACL')):
            gt = {c: int(row[c]) for c in ['ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus', 'Medial OA', 'Lateral OA', 'PF OA', 'Effusion', 'Synovitis', "Baker's", 'Contusion', 'Fracture']}
            
        diag_res = agent.process_study(uid, report, gt)
        row_res = {'StudyInstanceUID': uid}
        row_res.update(diag_res['predictions'])
        results.append(row_res)
        
        if (idx + 1) % 500 == 0 or (idx + 1) == len(subset):
            print(f"Completed {idx + 1}/{len(subset)} studies.")
            
    out_df = pd.DataFrame(results)
    out_df.to_csv('RSNA_Knee_Kaggle/predicted_diagnoses.csv', index=False)
    print("Saved predicted diagnoses to RSNA_Knee_Kaggle/predicted_diagnoses.csv")

if __name__ == '__main__':
    main()
