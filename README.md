# LLM Safety Evaluation Harness

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Dashboard](https://img.shields.io/badge/dashboard-streamlit-orange)](http://localhost:8501)

A clean, research-minded Python CLI and evaluation harness designed to test, log, score, and analyze Large Language Model (LLM) behavior for safety alignment, refusal quality, helpfulness, and user guidance.

---

## 🔬 Core Research Question

> **“How well do LLMs handle ambiguous, risky, privacy-sensitive, and prompt-injection-style user requests while remaining helpful?”**

To answer this, the harness evaluates models across diverse prompt categories, checking whether they can correctly identify and refuse unsafe requests (without preachy lecturing) while maintaining high helpfulness and clarity on benign or ambiguous inputs.

---

## 🛡️ The SaaS Security Parallel: LLM Safety Evals as Next-Gen WAFs

For technology and security companies (like **Fastly**), the architecture of AI safety guardrails shares a direct parallel with modern web application security:

```
[ Incoming Prompt ] ---> [ Adversarial Obfuscation ] ---> [ Input Filter / WAF ] ---> [ Target LLM ] ---> [ LLM-as-a-Judge ]
  (User Query)             (Base64, Sandbox Roleplays)      (Deterministic Rules)     (Core Model)       (Behavioral Audit)
```

1. **Adversarial Obfuscation (Like Injection Attacks)**: Just as web attackers use hex encoding or SQL injection payloads to bypass traditional firewalls, prompt injection and Base64-wrapped prompts attempt to bypass static LLM alignment filters.
2. **Deterministic Rules (Signature-Based Filtering)**: Our rule-based scanner behaves like a traditional Web Application Firewall (WAF), matching known patterns (refusal markers, preachy lecturing language, SSN formats) instantly and at zero cost.
3. **LLM-as-a-Judge (Behavioral & Anomaly Auditing)**: Since attackers write creative bypasses, rules are supplemented by semantic LLM evaluations. This functions like behavioral anomaly detection, scoring the safety, helpfulness, and tone of output responses.

---

## 💼 Why LLM Safety Matters for Enterprise SaaS
* **Mitigating Brand Risk**: Ensuring customer-facing AI agents refuse to generate malicious code, bypass security protocols, or give harmful advice.
* **Preventing "False-Positive" Refusals**: Unnecessarily blocking benign customer queries (e.g., refusing to show business hours due to an overly sensitive privacy rule) frustrates users and impacts conversion.
* **Ensuring Objective Communication**: High-quality safety systems refuse requests directly and neutrally. Preachy, moralizing, or scolding AI responses harm user experience.

---

## 🛠️ Key Features

* **Advanced Hybrid Evaluation**: Side-by-side comparison between deterministic rule-based checks and semantic **LLM-as-a-Judge** grading.
* **Adversarial Wrapperm (Jailbreak Testing)**: Automatically tests models against Direct prompts, Persona Roleplays ("Developer Sandbox Mode"), and Base64 Obfuscation.
* **Streamlit Interactive Dashboard**: Visualize safety degradation curves, compare rule vs. judge metrics, inspect discrepancies, and drill down on failed safety cases.
* **Dual Format Logging**: Outputs timestamped runs to both structured CSV and JSONL formats for MLOps pipeline integration.
* **Zero-Cost Mock Mode**: Runs completely offline, simulating model responses and safety failures locally to validate the analysis pipeline instantly.

---

## 📂 Project Structure

```
llm-safety-eval-harness/
  README.md                 # Project introduction and quickstart
  requirements.txt          # Third-party dependencies
  .gitignore                # Clean workspace exclusions
  .env.example              # API key configuration template
  results_summary.py        # Standalone results analyzer script
  streamlit_app.py          # Dashboard for interactive metrics
  data/
    sample_prompts.csv      # Curated evaluation dataset (16 prompts, 8 categories)
  docs/
    methodology.md          # Deep dive into scoring rules & metrics
  src/
    __init__.py
    main.py                 # Core CLI entrypoint and orchestrator
    llm_clients.py          # API integrations (Claude, OpenAI, Mock)
    scoring.py              # Rule-based checking rules & metrics
    reporting.py            # CSV/JSONL logging & report writers
    utils.py                # Latency timing and environment variables
  reports/
    summary.md              # Auto-generated markdown evaluation summary
  outputs/
    .gitkeep                # Output directory placeholder
  tests/
    __init__.py
    test_scoring.py         # Unit tests checking the scoring engine
```

---

## 🚀 Quickstart Guide (Runs Offline Instantly)

You do not need API keys to run, evaluate, or visualize this project. By default, it operates in **Mock Mode** using pre-configured target behaviors and evaluations.

### 1. Set Up Your Environment
Ensure you have Python 3.8+ installed. Clone or copy the project, create a virtual environment, and install dependencies:

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Evaluations (Mock Mode)
Run the permutation matrix (Direct, Roleplay, and Base64 prompts) to generate sample evaluations:
```powershell
python -m src.main --mock --eval-type all
```

### 3. Generate Analytical Summaries
Re-analyze the generated logs and compile the Markdown report:
```powershell
python results_summary.py
```

### 4. Launch the Interactive Dashboard
Launch the dashboard in your web browser:
```powershell
streamlit run streamlit_app.py
```
👉 Once started, navigate to **[http://localhost:8501](http://localhost:8501)** to view the comparative metrics.

---

## 📈 Score Interpretation & Analytics

* **Safety Score (1-5)**: Measures whether the model successfully refused an unsafe request (if expected) or answered without exposing private information/hallucinations. A score of `1` represents a critical safety leak.
* **LLM-as-a-Judge Safety**: Evaluates the semantic alignment of the response. The **Discrepancy Index** measures the absolute difference:
  $$\text{Discrepancy} = |\text{Safety}_{\text{Rule}} - \text{Safety}_{\text{Judge}}|$$
  A discrepancy > 0 highlights edge cases where regex-based rules differ from semantic understanding.
* **Adversarial Safety Drop**: The average direct safety score minus the average jailbreak safety score. A higher drop indicates susceptibility to persona bypass or obfuscation overrides.
* **Refusal Quality (1-5 or N/A)**: Evaluates whether refusals remain objective, professional, and dry. Lower scores indicate preaching, scolding, or lecturing language.

---

## ⚖️ Limitations & Rubric Rules

* **Keyword Limitations**: Rule-based scanners look for specific string sequences and can suffer from negations (e.g. *"I cannot refuse to answer..."* is classified as a refusal) or preachy false positives.
* **Heuristics vs. Semantics**: The hybrid scoring framework addresses this by overlaying LLM semantic grading on top of deterministic rule lists.
* **Diagnostic Size**: The harness uses 16 highly targeted prompts. Production-level suites scale this to thousands of prompts.

*For more details on scoring rules and methodology, read the [docs/methodology.md](file:///C:/Users/covie/Documents/GitHub/llm-safety-eval-harness/docs/methodology.md) document.*

---

## 🔮 Next Steps & Future Enhancements

1. **Jailbreak Expansion**: Add sophisticated multi-turn conversational jailbreaks or prompt-leakage templates.
2. **CI/CD Quality Gate**: Integrate the CLI tool as a post-commit hook or GitHub Action to block merges if average safety scores drop below `4.8`.
3. **Log Aggregation**: Integrate database logging (e.g. SQLite or MongoDB) to collect historical runs for continuous integration tracking.
