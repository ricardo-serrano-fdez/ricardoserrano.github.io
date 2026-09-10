"""
Diagnostic Interpreter Agent (Agent 2)
Processes Knee MRI study reports one StudyInstanceUID at a time,
structures the intermediate report, executes the decision tree,
and saves report.md and diagnosis.json in each study folder.
"""

import os
import sys
import json
import argparse
import pandas as pd
from typing import Dict, Any, Optional

from decision_tree import KneeDecisionTree
from report_structurer import generate_structured_report, generate_structured_report_from_llm
from llm_skill import generate_report_llm

TARGET_COLS = [
    'ACL', 'MCL', 'Medial Meniscus', 'Lateral Meniscus',
    'Medial OA', 'Lateral OA', 'PF OA', 'Effusion',
    'Synovitis', "Baker's", 'Contusion', 'Fracture'
]

class DiagnosticInterpreterAgent:
    def __init__(self, base_output_dir: str = 'RSNA_Knee_Kaggle/studies', mode: str = 'regex', llm_model: str = 'gpt-4o-mini', api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.base_output_dir = base_output_dir
        self.mode = mode.lower()
        self.llm_model = llm_model
        self.api_key = api_key
        self.base_url = base_url
        os.makedirs(self.base_output_dir, exist_ok=True)

    def process_study(self, study_uid: str, report_text: str, ground_truth: Optional[Dict[str, int]] = None, mode: Optional[str] = None) -> Dict[str, Any]:
        """Processes a single StudyInstanceUID."""
        active_mode = (mode or self.mode).lower()
        study_folder = os.path.join(self.base_output_dir, str(study_uid))
        os.makedirs(study_folder, exist_ok=True)

        if active_mode in ['llm', 'hybrid']:
            llm_res = generate_report_llm(
                raw_report=report_text,
                study_uid=study_uid,
                model=self.llm_model,
                api_key=self.api_key,
                base_url=self.base_url
            )
            predictions = llm_res.get('diagnoses', {})
            audit_trail = llm_res.get('reasoning', {})
            md_content = generate_structured_report_from_llm(study_uid, report_text, llm_res)
        else:
            eval_result = KneeDecisionTree.evaluate_all(report_text)
            predictions = eval_result['predictions']
            audit_trail = eval_result['audit_trail']
            md_content = generate_structured_report(study_uid, report_text, predictions)

        # Write intermediate report (.md)
        report_path = os.path.join(study_folder, 'report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # Write diagnosis output (.json)
        diag_data = {
            'StudyInstanceUID': study_uid,
            'mode_used': active_mode,
            'predictions': predictions,
            'audit_trail': audit_trail,
            'ground_truth': ground_truth
        }
        diag_path = os.path.join(study_folder, 'diagnosis.json')
        with open(diag_path, 'w', encoding='utf-8') as f:
            json.dump(diag_data, f, indent=2, ensure_ascii=False)

        return diag_data

    def process_csv(self, csv_path: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Processes train.csv row by row."""
        df = pd.read_csv(csv_path)
        if limit:
            df = df.head(limit)

        print(f"Agent starting processing on {len(df)} studies from {csv_path}...")
        results = []
        for idx, row in df.iterrows():
            study_uid = str(row['StudyInstanceUID'])
            report_text = str(row['Report'])
            gt = None
            if pd.notnull(row.get('ACL')):
                gt = {col: int(row[col]) for col in TARGET_COLS if pd.notnull(row.get(col))}

            diag_res = self.process_study(study_uid, report_text, gt)
            row_res = {'StudyInstanceUID': study_uid}
            row_res.update(diag_res['predictions'])
            results.append(row_res)

            if (idx + 1) % 100 == 0 or (idx + 1) == len(df):
                print(f"Processed {idx + 1}/{len(df)} studies...")

        return pd.DataFrame(results)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Diagnostic Interpreter Agent')
    parser.add_argument('--csv', default='RSNA_Knee_Kaggle/train.csv', help='Path to train.csv')
    parser.add_argument('--uid', default=None, help='Single StudyInstanceUID to process')
    parser.add_argument('--limit', type=int, default=None, help='Number of rows to process')
    parser.add_argument('--mode', choices=['regex', 'llm', 'hybrid'], default='regex', help='Inference mode')
    parser.add_argument('--model', default='gpt-4o-mini', help='LLM model name')
    parser.add_argument('--api_key', default=None, help='LLM API key')
    parser.add_argument('--base_url', default=None, help='OpenAI compatible Base URL')
    args = parser.parse_args()

    agent = DiagnosticInterpreterAgent(mode=args.mode, llm_model=args.model, api_key=args.api_key, base_url=args.base_url)
    if args.uid:
        df = pd.read_csv(args.csv)
        match = df[df['StudyInstanceUID'] == args.uid]
        if not match.empty:
            row = match.iloc[0]
            gt = {col: int(row[col]) for col in TARGET_COLS if pd.notnull(row.get(col))} if pd.notnull(row.get('ACL')) else None
            res = agent.process_study(args.uid, str(row['Report']), gt)
            print(f"Successfully processed Study UID ({args.mode} mode): {args.uid}")
            print(json.dumps(res, indent=2))
        else:
            print(f"Study UID {args.uid} not found in {args.csv}")
    else:
        out_df = agent.process_csv(args.csv, limit=args.limit)
        out_df.to_csv('RSNA_Knee_Kaggle/predicted_diagnoses.csv', index=False)
        print("Predictions saved to RSNA_Knee_Kaggle/predicted_diagnoses.csv")
