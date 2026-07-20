# LLM Safety Evaluation & Red-Teaming Harness

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Dashboard](https://img.shields.io/badge/dashboard-streamlit-orange)](http://localhost:8501)
[![Findings](https://img.shields.io/badge/research-findings.md-purple)](docs/findings.md)

A research-minded Python harness for red-teaming Large Language Models (LLMs), evaluating alignment boundaries, scoring refusal quality, and analyzing adversarial robustness across multi-turn jailbreaks and context injection vectors.

---

## 🔬 Core Research Questions & Key Findings

> **“How do model scale and refusal formatting affect adversarial robustness against multi-turn jailbreaks, indirect prompt injection, and borderline dual-use queries?”**

### Key Research Findings Overview
Read our full research note: **[docs/findings.md](docs/findings.md)**

1. **Model Capacity & Refusal Discrepancies**:
   * **Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)**: Achieved a high rule-based safety score (**4.43 / 5.0**) and a low **Discrepancy Index (0.63)** because its refusal responses adhere strictly to standardized prefix templates.
   * **Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)**: Achieved high semantic safety (**4.12 / 5.0** by LLM-as-a-Judge) but a lower rule score (**2.91 / 5.0**) and higher **Discrepancy Index (1.21)**. Sonnet's refusal style is highly educational and objective rather than template-based, exposing the false-positive limitations of static regex scanners.
2. **Threat Vector Hierarchy**:
   * Direct harmful queries are consistently blocked across both models.
   * Indirect context injection (`context_injection`) and multi-turn persona building (`multi_turn_jailbreak`) represent the highest threat vectors, causing the largest **Adversarial Safety Drop**.

---

## 🛡️ Architecture & Hybrid Evaluation Framework

The harness combines fast, deterministic rule-based checks with an automated **LLM-as-a-Judge** scoring engine:

```
[ Input Query ] ---> [ Adversarial Wrappers ] ---> [ Multi-Turn & Target LLM ] ---> [ Hybrid Scorer ] ---> [ Discrepancy & Reports ]
                      (Roleplay, Base64,             (Haiku 4.5 / Sonnet 4.5)         (Rule Engine +          (CSV, JSONL, Streamlit,
                       Multi-Turn |||)                                                 LLM-as-a-Judge)           findings.md)
```

1. **Adversarial Wrappers**: Automatically compiles prompt payloads into direct requests, persona overrides (`"Developer Sandbox Mode"`), Base64 obfuscations, and multi-turn dialogue histories (`|||` delimiter).
2. **Deterministic Heuristic Rules**: Evaluates response strings instantly using regex pattern matching for refusal markers, PII leakage, preachy lecturing language, and alternative guidance checks.
3. **LLM-as-a-Judge**: Prompts a frontier model under a strict 1–5 rubric to assess semantic safety, refusal tone, and helpfulness, producing a quantitative **Discrepancy Index**:
   $$\text{Discrepancy} = |\text{Safety}_{\text{Rule}} - \text{Safety}_{\text{Judge}}|$$

---

## 🛠️ Key Features

* **Empirical Multi-Model Comparison**: Evaluates smaller/faster models against frontier models on identical benchmark suites.
* **Multi-Turn Jailbreak Engine**: Full conversational history tracking across multi-turn prompt sequences.
* **Hybrid Judge & Discrepancy Analysis**: Detects rule-based false positives and false negatives by measuring semantic delta against an LLM Judge.
* **Safety-Constrained Benchmark Dataset**: 58 curated, non-actionable threat prompts across 12 safety and threat categories in `data/sample_prompts.csv`.
* **Interactive Streamlit Dashboard**: Visualize adversarial degradation curves, inspect failing safety cases, and analyze discrepancy metrics.
* **Zero-Cost Offline Mock Mode**: Run evaluations offline with mock model behavior for fast local iteration.

---

## 📂 Project Structure

```
llm-safety-eval-harness/
  README.md                 # Research overview and quickstart
  requirements.txt          # Third-party dependencies
  .gitignore                # Clean workspace exclusions
  .env.example              # API key configuration template
  results_summary.py        # Standalone results analyzer script
  streamlit_app.py          # Streamlit metrics visualization dashboard
  data/
    sample_prompts.csv      # Expanded safety dataset (58 prompts, 12 categories)
  docs/
    methodology.md          # Scoring rubrics, threat categories, & metrics
    findings.md             # Empirical research note and comparative results
  src/
    __init__.py
    main.py                 # Core CLI entrypoint & multi-turn evaluation runner
    llm_clients.py          # API integrations (Claude, OpenAI, Mock)
    scoring.py              # Rule-based checking heuristics & LLM-as-a-Judge
    reporting.py            # CSV/JSONL result loggers & markdown generator
    utils.py                # Timing utilities & environment parsing
  reports/
    summary.md              # Auto-generated markdown evaluation summary
  outputs/
    eval_results_haiku_real.csv    # Real run benchmark dataset for Haiku 4.5
    eval_results_sonnet_real.csv   # Real run benchmark dataset for Sonnet 4.5
  tests/
    test_scoring.py         # Pytest suite covering false-positives, multi-turn, & rubrics
```

---

## 🚀 Quickstart Guide

### 1. Set Up Environment & Install Dependencies

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows (PowerShell)
# source venv/bin/activate    # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Offline Mock Evaluation (No API Key Required)
Run the full benchmark suite across all wrappers in mock mode:
```powershell
python -m src.main --mock --eval-type all
```

### 3. Run Live Comparative Model Evaluation
Configure your Anthropic API key in `.env` (`ANTHROPIC_API_KEY=sk-ant-...`), then run:
```powershell
# Evaluate smaller model (Claude Haiku 4.5)
python -m src.main --model claude-haiku-4-5-20251001 --eval-type all

# Evaluate frontier model (Claude Sonnet 4.5)
python -m src.main --model claude-sonnet-4-5-20250929 --eval-type all
```

### 4. Run Pytest Verification Suite
```powershell
pytest
```

### 5. Launch Interactive Streamlit Dashboard
```powershell
streamlit run streamlit_app.py
```
Navigate to **[http://localhost:8501](http://localhost:8501)** to explore comparative metrics and safety failure distributions.

---

## 📜 Citation & Research Reference

If referencing this harness in AI safety or alignment work, please cite:
```bibtex
@misc{llm_safety_eval_harness_2026,
  author = {AI Safety Research Team},
  title = {LLM Safety Evaluation Harness: Hybrid Red-Teaming and Multi-Turn Jailbreak Benchmarking},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/christophersoviedo/llm-safety-eval-harness}}
}
```
