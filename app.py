"""Streamlit interface for a safe, local Text-to-SQL retail demo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from openai import APIStatusError


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from retail_assistant.database import DB_PATH, SCHEMA_DESCRIPTION, run_read_only_query  # noqa: E402
from retail_assistant.llm import MODEL, generate_sql, summarize_results  # noqa: E402


st.set_page_config(page_title="Retail Chat Analytics", page_icon="📊", layout="wide")
st.title("Retail Chat Analytics")
st.caption("Ask business questions in plain English. Inspect the generated SQL and results.")

st.info(
    "This demo uses synthetic retail data. Your question and a small sample of query results "
    "are sent to the OpenAI API to generate SQL and summarize the answer. Don’t connect private "
    "or production data to this demo."
)

if not os.getenv("OPENAI_API_KEY"):
    st.warning("Set `OPENAI_API_KEY` in your terminal before starting the app.")

if not DB_PATH.exists():
    st.warning("The demo database is missing. Run `python seed_demo_db.py` from the project folder.")

with st.expander("Demo schema and metric definition"):
    st.code(SCHEMA_DESCRIPTION, language="text")

with st.form("question_form"):
    question = st.text_input(
        "Business question",
        placeholder="Which product categories generated the most net sales last quarter?",
        max_chars=500,
    )
    submitted = st.form_submit_button("Ask the data", type="primary")

if submitted:
    if not question.strip():
        st.error("Enter a business question first.")
    elif len(question) > 500:
        st.error("Keep the question under 500 characters.")
    else:
        try:
            with st.spinner("Translating your question into SQL…"):
                plan = generate_sql(question.strip())

            if not plan["can_answer"]:
                st.warning(plan["note"] or "This demo schema cannot answer that question.")
            else:
                sql = plan["sql"].strip()
                with st.expander("Generated SQL", expanded=True):
                    st.code(sql, language="sql")

                with st.spinner("Running a read-only query…"):
                    columns, rows, truncated = run_read_only_query(sql)

                st.subheader("Results")
                if rows:
                    st.dataframe(pd.DataFrame(rows, columns=columns), use_container_width=True)
                else:
                    st.write("The query returned no rows.")
                if truncated:
                    st.caption("Showing the first 200 rows.")

                with st.spinner("Writing a short answer from the results…"):
                    answer = summarize_results(question.strip(), sql, columns, rows, truncated)
                st.subheader("Answer")
                st.write(answer)
                st.caption(f"Model: {MODEL} · Returned rows: {len(rows)}")
        except APIStatusError as error:
            if error.status_code == 429:
                st.error(
                    "The OpenAI API rejected this request (HTTP 429). Check the API project’s "
                    "remaining credits and rate limits in [API billing settings]"
                    "(https://platform.openai.com/settings/organization/billing/)."
                )
            else:
                st.error(f"OpenAI API request failed (HTTP {error.status_code}). Check the API response and try again.")
        except Exception as error:  # Keep SQL and setup errors visible during a portfolio demo.
            st.error(f"Could not answer this question: {error}")

with st.sidebar:
    st.header("Try asking")
    st.markdown(
        "- Which categories had the highest net sales?\n"
        "- Compare online and in-store sales by region.\n"
        "- What were the monthly sales trends in 2025?\n"
        "- Which loyalty tier placed the most orders?"
    )
    st.divider()
    st.caption("SQLite is opened read-only. Generated SQL is restricted to the demo tables.")
