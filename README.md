# Retail Chat Analytics

A small portfolio demo that translates plain-English retail questions into SQLite queries, runs them against a synthetic sales database, and summarizes the returned results.

## What it demonstrates

- Prompting an LLM to produce structured, schema-aware SQL plans.
- A normalized relational schema with customers, products, stores, orders, and order items.
- Safe query execution using a read-only SQLite connection, an SQLite authorizer, an allowed-function list, a query-work limit, and a 200-row result cap.
- Separating SQL generation from result explanation so the query and answer can be inspected.
- Synthetic, reproducible data generation; no real customer data is included.

## Requirements

- Python 3.10+
- An OpenAI API key with API billing enabled. ChatGPT/Codex subscriptions and API usage are billed separately.

## Run locally

From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python seed_demo_db.py
# Read the key silently so the key itself is not saved as a shell command.
read -s -p "OpenAI API key: " OPENAI_API_KEY; printf "\n"; export OPENAI_API_KEY
# Optional: choose another model available to your API project.
export OPENAI_MODEL="gpt-6-luna"
streamlit run app.py
```

On Windows PowerShell, set `$env:OPENAI_API_KEY` in the current terminal session without pasting the key into a chat or source file, then run `streamlit run app.py`.

The app opens in a browser at the local URL printed by Streamlit. The API key is read from the process environment and is never stored in the repository. Do not paste it into source code or commit it.

## Data and privacy

`seed_demo_db.py` creates 300 synthetic customers, 50 products, 6 stores, 1,200 orders, and roughly 3,000 order items across 2024–2025. Re-running the script recreates the database deterministically.

The app sends the question and database schema to OpenAI to generate SQL. It then sends the generated SQL and up to 20 synthetic result rows to OpenAI for a short explanation. API calls set `store=False`. Use only the included synthetic dataset in this version; connecting private business data needs a separate privacy, security, and access-control design.

## Query guardrails

The model is not trusted to enforce safety. Before execution, the app opens SQLite in read-only mode, sets `query_only`, authorizes only reads from the five demo tables and a short list of functions, rejects multi-statement input, limits query work, and caps returned rows. These controls are appropriate for this local demo, not a substitute for production security review.

## Suggested next improvements

1. Add chart selection for common result shapes.
2. Add a small evaluation set of representative questions with expected SQL and expected aggregates; measure execution accuracy and answer faithfulness.
3. Add examples of ambiguous questions and a clarification step before SQL generation.
4. Add a documented comparison of model quality and per-question API cost.

## Resume wording after you run and validate it

> Built a Text-to-SQL analytics assistant that uses the OpenAI Responses API to translate natural-language questions into schema-aware SQLite queries over a synthetic retail dataset; added read-only query safeguards and plain-English result summaries.

Only include claims you personally verify and can explain. Add a GitHub/demo link once you publish the project yourself.
