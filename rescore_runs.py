import csv
import os
import glob
import argparse
from src.scoring import score_response
from src.utils import parse_bool
from src.reporting import compile_summary_data, write_markdown_report

def main():
    parser = argparse.ArgumentParser(
        description="Rescore evaluation runs using updated refusal rules."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=None, 
        help="Path to evaluation CSV file. If omitted, uses the latest file in the outputs directory."
    )
    args = parser.parse_args()

    # 1. Load the baseline prompts to get should_refuse mapping
    prompts_map = {}
    with open("data/sample_prompts.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts_map[row["prompt_id"]] = parse_bool(row.get("should_refuse", "FALSE"))

    # 2. Select file to rescore
    target_csv = args.input
    if not target_csv:
        csv_files = glob.glob("outputs/eval_results_*.csv")
        if not csv_files:
            print("[ERROR] No evaluation CSV logs found to rescore.")
            return
        target_csv = max(csv_files, key=os.path.getmtime)
    
    if not os.path.exists(target_csv):
        print(f"[ERROR] Specified file not found: {target_csv}")
        return

    print(f"[INFO] Rescoring run log: {target_csv} ...")

    # 3. Read and update the rows
    rows = []
    headers = []
    with open(target_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            pid = row["prompt_id"]
            should_refuse = prompts_map.get(pid, False)
            
            # Recalculate rule-based scores
            scores = score_response(
                category=row["category"],
                prompt=row["prompt"],
                response=row["response"],
                should_refuse=should_refuse,
                expected_behavior=row["expected_behavior"]
            )
            
            row["safety_score"] = scores["safety_score"]
            row["helpfulness_score"] = scores["helpfulness_score"]
            row["refusal_quality_score"] = scores["refusal_quality_score"]
            row["notes"] = scores["notes"]
            
            # Recompute discrepancy
            judge_safety = float(row.get("judge_safety_score", 3.0))
            row["score_discrepancy"] = abs(scores["safety_score"] - judge_safety)
            
            rows.append(row)

    # 4. Write back to the same CSV
    with open(target_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
            
    print("[SUCCESS] Rescoring completed successfully.")

if __name__ == "__main__":
    main()

