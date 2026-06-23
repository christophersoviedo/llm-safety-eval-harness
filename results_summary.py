import argparse
import os
import sys
import glob
import csv
from typing import List, Dict, Any

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.reporting import compile_summary_data, write_markdown_report

def get_latest_csv(outputs_dir: str) -> str:
    """Find the latest CSV file in the outputs directory."""
    search_pattern = os.path.join(outputs_dir, "eval_results_*.csv")
    csv_files = glob.glob(search_pattern)
    if not csv_files:
        return ""
    # Sort by modification time
    return max(csv_files, key=os.path.getmtime)

def load_results_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load logged evaluation entries from a CSV output file."""
    results = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_typed = dict(row)
            # Reconstruct scores
            for key in ["safety_score", "helpfulness_score", "judge_safety_score", "judge_helpfulness_score"]:
                if key in row and row[key] not in (None, "N/A", "none", "", "nan"):
                    try:
                        row_typed[key] = int(row[key])
                    except ValueError:
                        pass
                        
            # Reconstruct score_discrepancy & latency_seconds
            for key in ["score_discrepancy", "latency_seconds"]:
                if key in row and row[key] not in (None, "N/A", "none", "", "nan"):
                    try:
                        row_typed[key] = float(row[key])
                    except ValueError:
                        pass

            results.append(row_typed)
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Results Summary utility - Analyze pre-existing LLM safety runs and regenerate reports."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=None, 
        help="Path to evaluation CSV file. If omitted, uses the latest file in the outputs directory."
    )
    parser.add_argument(
        "--output-report", 
        type=str, 
        default="reports/summary.md", 
        help="Path where markdown report should be saved (default: reports/summary.md)."
    )
    parser.add_argument(
        "--outputs-dir", 
        type=str, 
        default="outputs", 
        help="Directory to check for latest CSV files if --input is not specified."
    )
    
    args = parser.parse_args()
    
    csv_file = args.input
    if not csv_file:
        csv_file = get_latest_csv(args.outputs_dir)
        if not csv_file:
            print(f"[ERROR] No CSV file found in output directory '{args.outputs_dir}'.")
            print("Please run the evaluation runner first using: python -m src.main --mock")
            sys.exit(1)
        print(f"[INFO] Auto-selected latest evaluation CSV: {csv_file}")
    else:
        if not os.path.exists(csv_file):
            print(f"[ERROR] Specified file not found: {csv_file}")
            sys.exit(1)
            
    print(f"[INFO] Loading results from: {csv_file} ...")
    results = load_results_from_csv(csv_file)
    
    if not results:
        print("[ERROR] No entries found in the specified CSV.")
        sys.exit(1)
        
    model_name = results[0].get("model", "Unknown Model")
    
    print("[INFO] Computing summary metrics...")
    summary = compile_summary_data(results)
    
    print(f"[INFO] Saving markdown report to: {args.output_report} ...")
    write_markdown_report(summary, args.output_report, model_name)
    
    # Display summary to console
    print("\n" + "=" * 60)
    print(" SUMMARY STATISTICS (ADVANCED HYBRID EVALUATION)")
    print("=" * 60)
    print(f"Model Evaluated:         {model_name}")
    print(f"Source File:             {csv_file}")
    print(f"Total Permutations Run:  {summary['total_cases']}")
    print(f"Safety Failures (Any):   {summary['failed_safety_count']}")
    print(f"Overall Safety Avg:      Rule={summary['overall_avg_safety']}/5.0 | Judge={summary['overall_avg_judge_safety']}/5.0")
    print(f"Overall Helpfulness Avg: Rule={summary['overall_avg_helpfulness']}/5.0 | Judge={summary['overall_avg_judge_helpfulness']}/5.0")
    print(f"Avg Score Discrepancy:   {summary['avg_discrepancy']:.2f}")
    print(f"Best Category:           {summary['best_category']}")
    print(f"Worst Category:          {summary['worst_category']}")
    print("=" * 60)
    print("[SUCCESS] Summary report updated successfully.")

if __name__ == "__main__":
    main()
