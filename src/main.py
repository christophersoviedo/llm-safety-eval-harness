import argparse
import sys
import os
import csv
from datetime import datetime
import uuid

# Add the parent directory to sys.path to support running as module or direct script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import get_api_key, parse_bool
from src.llm_clients import ClaudeClient, OpenAIClient, MockClient
from src.scoring import score_response, LLMJudge
from src.adversarial import compile_prompt
from src.reporting import write_results, compile_summary_data, write_markdown_report

def main():
    parser = argparse.ArgumentParser(
        description="LLM Safety Evaluation Harness - A research-minded tool to evaluate LLM alignment."
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="claude-sonnet-4-5-20250929",
        help="Model identifier (e.g. gpt-4o-mini, claude-sonnet-4-5-20250929)."
    )
    parser.add_argument(
        "--mock", 
        action="store_true", 
        help="Run evaluations in offline mock mode without making API calls."
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit evaluation to the first N prompts."
    )
    parser.add_argument(
        "--category", 
        type=str, 
        default=None, 
        help="Filter prompts by a specific category."
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.0, 
        help="Generation temperature (default: 0.0)."
    )
    parser.add_argument(
        "--max-tokens", 
        type=int, 
        default=1000, 
        help="Maximum generation tokens (default: 1000)."
    )
    parser.add_argument(
        "--input-file", 
        type=str, 
        default="data/sample_prompts.csv",
        help="Path to evaluation dataset CSV (default: data/sample_prompts.csv)."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="outputs",
        help="Directory to save evaluation results (default: outputs)."
    )
    parser.add_argument(
        "--eval-type",
        type=str,
        default="direct",
        choices=["direct", "jailbreak", "all"],
        help="Evaluation type to run (direct, jailbreak [roleplay + base64], or all) (default: direct)."
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default="claude-sonnet-4-5-20250929",
        help="Model used as the LLM-as-a-Judge (default: claude-sonnet-4-5-20250929)."
    )
    args = parser.parse_args()

    # Determine execution mode and setup client
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    print("=" * 60)
    print(f"Starting LLM Safety Evaluation Run (ID: {run_id})")
    print("=" * 60)

    # API key checks & fallback logic
    # API key checks & fallback logic
    is_openai_model = "gpt" in args.model.lower()
    provider = "openai" if is_openai_model else "anthropic"
    api_key = get_api_key(provider)
    
    if args.mock:
        print("[MODE] Running in MOCK Mode. (Offline, local simulation)")
        client = MockClient(model_name=f"mock-{args.model}")
    elif not api_key:
        print(f"[WARNING] No API key found for provider '{provider.upper()}'.")
        print("[WARNING] Automatically falling back to MOCK mode so the runner can complete.")
        args.mock = True
        client = MockClient(model_name=f"mock-{args.model}")
    else:
        print(f"[MODE] Running in LIVE Mode. Provider: {provider.upper()}, Model: {args.model}")
        try:
            if is_openai_model:
                client = OpenAIClient(api_key=api_key, model_name=args.model)
            else:
                client = ClaudeClient(api_key=api_key, model_name=args.model)
        except Exception as e:
            print(f"[ERROR] Failed to initialize client for model {args.model}: {e}")
            print("[ERROR] Swapping to Mock Client fallback.")
            client = MockClient(model_name=f"mock-{args.model}")
            args.mock = True

    # Setup LLM Judge Client
    judge_openai = "gpt" in args.judge_model.lower()
    judge_provider = "openai" if judge_openai else "anthropic"
    judge_key = get_api_key(judge_provider)
    
    if args.mock:
        judge_client = MockClient(model_name=f"mock-{args.judge_model}")
    elif not judge_key:
        print(f"[WARNING] No API key found for judge provider '{judge_provider.upper()}'. Mocking the judge.")
        judge_client = MockClient(model_name=f"mock-{args.judge_model}")
    else:
        try:
            if judge_openai:
                judge_client = OpenAIClient(api_key=judge_key, model_name=args.judge_model)
            else:
                judge_client = ClaudeClient(api_key=judge_key, model_name=args.judge_model)
        except Exception as e:
            print(f"[ERROR] Failed to initialize judge client {args.judge_model}: {e}. Mocking judge.")
            judge_client = MockClient(model_name=f"mock-{args.judge_model}")

    judge = LLMJudge(judge_client)
    print(f"[JUDGE] Safety Evaluator: {judge_client.model_name}")

    # Check and load dataset
    if not os.path.exists(args.input_file):
        print(f"[CRITICAL] Dataset file not found: {args.input_file}")
        sys.exit(1)

    prompts = []
    try:
        with open(args.input_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append(row)
    except Exception as e:
        print(f"[CRITICAL] Failed to parse prompt file: {e}")
        sys.exit(1)

    # Apply filters
    if args.category:
        filtered_prompts = [p for p in prompts if p["category"].strip() == args.category.strip()]
        print(f"[FILTER] Applied category filter: '{args.category}' ({len(filtered_prompts)}/{len(prompts)} matches)")
        prompts = filtered_prompts

    if args.limit is not None:
        prompts = prompts[:args.limit]
        print(f"[LIMIT] Restricting run to first {args.limit} prompts.")

    if not prompts:
        print("[WARNING] No prompts left to evaluate after applying filters.")
        sys.exit(0)

    # Determine eval types to run
    eval_types = []
    if args.eval_type in ("direct", "all"):
        eval_types.append("direct")
    if args.eval_type in ("jailbreak", "all"):
        eval_types.append("roleplay_jailbreak")
        eval_types.append("base64_jailbreak")

    total_permutations = len(prompts) * len(eval_types)
    print(f"\n[RUNNER] Evaluating {len(prompts)} prompts across {len(eval_types)} wrappers (Total: {total_permutations} cases)...")

    results = []
    case_num = 1
    
    for i, p in enumerate(prompts, 1):
        prompt_id = p.get("prompt_id", f"P{i:03d}")
        category = p.get("category", "unspecified")
        prompt_text = p.get("prompt", "")
        should_refuse = parse_bool(p.get("should_refuse", "FALSE"))
        expected_behavior = p.get("expected_behavior", "")

        for etype in eval_types:
            # Wrap the prompt
            compiled_prompt = compile_prompt(prompt_text, etype)
            
            print(f" [{case_num}/{total_permutations}] {prompt_id} [{category}] type={etype} ... ", end="", flush=True)
            
            # Call API client
            res = client.generate_response(
                prompt=compiled_prompt,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )
            
            response_text = res["response"]
            latency = res["latency_seconds"]
            error_msg = res["error"]
            
            if error_msg:
                print(f"FAILED (Error: {error_msg})")
                scores = {
                    "safety_score": 1,
                    "refusal_quality_score": "N/A",
                    "helpfulness_score": 1,
                    "notes": f"API Error: {error_msg}"
                }
                judge_scores = {
                    "safety_score": 1,
                    "refusal_quality_score": "N/A",
                    "helpfulness_score": 1,
                    "notes": f"API Error: {error_msg}"
                }
            else:
                print("OK")
                # Calculate Rule-Based Scores
                scores = score_response(
                    category=category,
                    prompt=prompt_text,
                    response=response_text,
                    should_refuse=should_refuse,
                    expected_behavior=expected_behavior
                )
                # Calculate LLM Judge Scores
                judge_scores = judge.evaluate_response(
                    category=category,
                    prompt=prompt_text,
                    response=response_text,
                    should_refuse=should_refuse,
                    expected_behavior=expected_behavior,
                    eval_type=etype
                )

            # Safety discrepancy
            discrepancy = abs(scores["safety_score"] - judge_scores["safety_score"])

            # Log entry
            result_entry = {
                "run_id": run_id,
                "prompt_id": prompt_id,
                "category": category,
                "prompt": prompt_text,
                "eval_type": etype,
                "model": client.model_name,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "safety_score": scores["safety_score"],
                "helpfulness_score": scores["helpfulness_score"],
                "refusal_quality_score": scores["refusal_quality_score"],
                "notes": scores["notes"],
                "judge_safety_score": judge_scores["safety_score"],
                "judge_helpfulness_score": judge_scores["helpfulness_score"],
                "judge_refusal_quality_score": judge_scores["refusal_quality_score"],
                "judge_notes": judge_scores["notes"],
                "score_discrepancy": discrepancy,
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
                "latency_seconds": latency,
                "error": error_msg or "",
                "expected_behavior": expected_behavior
            }
            results.append(result_entry)
            case_num += 1

    # Save to outputs
    print("\n[REPORTING] Writing results to outputs directory...")
    csv_path, jsonl_path = write_results(results, args.output_dir)
    print(f" -> CSV: {csv_path}")
    print(f" -> JSONL: {jsonl_path}")

    # Compile report
    print("[REPORTING] Analyzing results and generating reports/summary.md...")
    summary = compile_summary_data(results)
    report_path = os.path.join("reports", "summary.md")
    write_markdown_report(summary, report_path, client.model_name)
    print(f" -> Summary Report: {report_path}")

    # Display clean console summary
    print("\n" + "=" * 60)
    print(" ADVANCED EVALUATION COMPLETED")
    print("=" * 60)
    print(f"Model Evaluated:         {client.model_name}")
    print(f"Judge Evaluator:         {judge_client.model_name}")
    print(f"Total Permutations Run:  {summary['total_cases']}")
    print(f"Safety Failures:         {summary['failed_safety_count']}")
    print(f"Overall Safety Avg:      Rule={summary['overall_avg_safety']}/5.0 | Judge={summary['overall_avg_judge_safety']}/5.0")
    print(f"Overall Helpfulness Avg: Rule={summary['overall_avg_helpfulness']}/5.0 | Judge={summary['overall_avg_judge_helpfulness']}/5.0")
    print(f"Avg Score Discrepancy:   {summary['avg_discrepancy']:.2f}")
    print(f"Best Category (Safety):  {summary['best_category']}")
    print(f"Worst Category (Safety): {summary['worst_category']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
