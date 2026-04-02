import streamlit as st

# =========================
# 🔐 PIN Authentication
# =========================
APP_PIN = st.secrets["APP_PIN"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Enter PIN")

    pin_input = st.text_input(
        "4-digit PIN",
        type="password",
        max_chars=4
    )

    if st.button("Unlock", use_container_width=True):
        if pin_input == APP_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN")

    st.stop()

from supabase import create_client
from datetime import date
import os

# -----------------------
# CONFIG
# -----------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Life Memory Console", layout="wide")

# -----------------------
# UI
# -----------------------
st.title("Life Memory Console")

tab1, tab2, tab3 = st.tabs(["➕ Journal", "🧠 Decisions", "📖 View Data"])

# -----------------------
# JOURNAL ENTRY
# -----------------------
with tab1:
    st.subheader("Add Journal Entry")

    entry_date = st.date_input("Date", value=date.today())

    entry_type = st.selectbox(
        "Type",
        ["journal", "learning", "decision", "reflection", "project"]
    )

    text = st.text_area("Entry", height=200)

    tags_raw = st.text_input("Tags (comma separated)")

    if st.button("Save Journal Entry"):
        if not text.strip():
            st.error("Entry text cannot be empty")
        else:
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

            supabase.table("journal_entries").insert({
                "entry_date": str(entry_date),
                "text": text,
                "type": entry_type,
                "tags": tags
            }).execute()

            st.success("Journal entry saved")
            st.rerun()

# -----------------------
# DECISIONS
# -----------------------
with tab2:
    st.subheader("Add Decision")

    decision_date = st.date_input("Decision date", value=date.today(), key="dd")

    title = st.text_input("Title")

    context = st.text_area("Context", height=120)
    choice = st.text_area("Choice made", height=80)
    reasoning = st.text_area("Reasoning", height=120)
    outcome = st.text_area("Outcome / Result", height=80)

    d_tags_raw = st.text_input("Tags (comma separated)", key="dtags")

    if st.button("Save Decision"):
        tags = [t.strip() for t in d_tags_raw.split(",") if t.strip()]

        supabase.table("decisions").insert({
            "decision_date": str(decision_date),
            "title": title,
            "context": context,
            "choice": choice,
            "reasoning": reasoning,
            "outcome": outcome,
            "tags": tags
        }).execute()

        st.success("Decision saved")
        st.rerun()

# -----------------------
# VIEW DATA
# -----------------------
with tab3:
    st.subheader("Browse Memory")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Journal Entries")

        j_limit = st.slider("How many journal entries?", 5, 100, 20)

        journal = supabase.table("journal_entries") \
            .select("*") \
            .order("entry_date", desc=True) \
            .limit(j_limit) \
            .execute()

        for j in journal.data:
            with st.expander(f"{j['entry_date']} | {j['type']}"):
                st.write(j["text"])
                if j["tags"]:
                    st.caption("Tags: " + ", ".join(j["tags"]))

    with col2:
        st.markdown("### Decisions")

        d_limit = st.slider("How many decisions?", 5, 100, 20)

        decisions = supabase.table("decisions") \
            .select("*") \
            .order("decision_date", desc=True) \
            .limit(d_limit) \
            .execute()

        for d in decisions.data:
            with st.expander(f"{d['decision_date']} | {d.get('title','')}"):
                st.markdown("**Context**")
                st.write(d["context"])
                st.markdown("**Choice**")
                st.write(d["choice"])
                st.markdown("**Reasoning**")
                st.write(d["reasoning"])
                st.markdown("**Outcome**")
                st.write(d["outcome"])
                if d["tags"]:
                    st.caption("Tags: " + ", ".join(d["tags"]))
