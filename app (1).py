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
from datetime import date, timedelta
import os

# -----------------------
# CONFIG
# -----------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Life Memory Console", layout="wide")

# -----------------------
# HABITS CONFIG
# Stored in journal_entries as type="habit", text=habit_id, tags=["habit", category]
# -----------------------
HABITS = [
    {"id": "fixed_wake_up",        "label": "Fixed wake-up time",          "category": "sleep",       "note": "Same time every day"},
    {"id": "no_screens_before_bed", "label": "No screens 30 min before bed","category": "sleep",       "note": "Read, stretch, or journal instead"},
    {"id": "morning_sunlight",      "label": "Morning sunlight within 30 min","category": "sleep",     "note": "10 min outside — sets your circadian clock"},
    {"id": "deep_work_block",       "label": "1 deep work block (90 min)",  "category": "focus",       "note": "Phone away, one task, notifications off"},
    {"id": "write_top3_tasks",      "label": "Write tomorrow's top 3 tasks","category": "focus",       "note": "Every evening — 2 min, eliminates morning drift"},
    {"id": "no_social_before_noon", "label": "No social media before noon", "category": "focus",       "note": "Protect your peak cognitive hours"},
]

HABIT_IDS = [h["id"] for h in HABITS]

# -----------------------
# HABIT HELPERS
# -----------------------

def fetch_habit_rows(from_date: date, to_date: date) -> list[dict]:
    """Fetch all habit journal entries in a date range."""
    result = supabase.table("journal_entries") \
        .select("id, entry_date, text") \
        .eq("type", "habit") \
        .gte("entry_date", str(from_date)) \
        .lte("entry_date", str(to_date)) \
        .execute()
    return result.data or []


def get_checked_set(rows: list[dict], for_date: date) -> dict[str, str]:
    """Return {habit_id: row_id} for a given date."""
    date_str = str(for_date)
    return {r["text"]: r["id"] for r in rows if r["entry_date"] == date_str}


def check_habit(habit_id: str, for_date: date):
    supabase.table("journal_entries").insert({
        "entry_date": str(for_date),
        "text": habit_id,
        "type": "habit",
        "tags": ["habit", next(h["category"] for h in HABITS if h["id"] == habit_id)]
    }).execute()


def uncheck_habit(row_id: str):
    supabase.table("journal_entries").delete().eq("id", row_id).execute()


def compute_streak(habit_id: str, rows: list[dict]) -> int:
    """Count consecutive days ending today (or yesterday if today not done)."""
    done_dates = {r["entry_date"] for r in rows if r["text"] == habit_id}
    today_str = str(date.today())
    streak = 0
    d = date.today()
    # If not done today, start checking from yesterday
    if today_str not in done_dates:
        d -= timedelta(days=1)
    for _ in range(30):
        if str(d) in done_dates:
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak


# -----------------------
# UI
# -----------------------
st.title("Life Memory Console")

tab1, tab2, tab3, tab4 = st.tabs(["➕ Journal", "🧠 Decisions", "📖 View Data", "✅ Habits"])

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
            .neq("type", "habit") \
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

# -----------------------
# HABITS TAB
# -----------------------
with tab4:
    st.subheader("Daily Habits")

    today = date.today()
    habit_date = st.date_input("Tracking date", value=today, key="habit_date")

    # Fetch last 30 days of habit rows for streaks + week dots
    rows_30 = fetch_habit_rows(habit_date - timedelta(days=30), habit_date)
    checked_today = get_checked_set(rows_30, habit_date)

    # --- Summary metrics ---
    done_count = sum(1 for h in HABITS if h["id"] in checked_today)
    total = len(HABITS)

    m1, m2, m3 = st.columns(3)
    m1.metric("Done today", f"{done_count} / {total}")
    min_streak = min(compute_streak(h["id"], rows_30) for h in HABITS)
    m2.metric("Lowest streak", f"{min_streak} days")
    week_rows = fetch_habit_rows(habit_date - timedelta(days=6), habit_date)
    week_done = sum(
        1 for h in HABITS
        for d_offset in range(7)
        if h["id"] in get_checked_set(week_rows, habit_date - timedelta(days=d_offset))
    )
    week_pct = round(week_done / (total * 7) * 100)
    m3.metric("This week", f"{week_pct}%")

    st.divider()

    # --- Habit rows ---
    categories = ["sleep", "focus"]
    category_labels = {"sleep": "😴 Sleep & Energy", "focus": "🧠 Focus & Productivity"}

    for cat in categories:
        st.markdown(f"**{category_labels[cat]}**")
        cat_habits = [h for h in HABITS if h["category"] == cat]

        for habit in cat_habits:
            hid = habit["id"]
            is_checked = hid in checked_today
            streak = compute_streak(hid, rows_30)

            # 7-day dot string
            dots = ""
            for d_offset in range(6, -1, -1):
                d_check = habit_date - timedelta(days=d_offset)
                day_checked = get_checked_set(rows_30, d_check)
                if d_offset == 0:
                    dots += "🔵" if is_checked else "⚪"
                else:
                    dots += "🟢" if hid in day_checked else "⚫"

            col_check, col_info, col_streak = st.columns([0.5, 5, 1.5])

            with col_check:
                new_val = st.checkbox(
                    label=hid,
                    value=is_checked,
                    key=f"habit_{hid}_{habit_date}",
                    label_visibility="collapsed"
                )

            with col_info:
                st.markdown(f"**{habit['label']}**")
                st.caption(f"{habit['note']}  ·  {dots}")

            with col_streak:
                badge = f"🔥 {streak}d" if streak >= 3 else f"{streak}d"
                st.markdown(f"<div style='padding-top:6px; font-size:13px; color:gray;'>{badge}</div>", unsafe_allow_html=True)

            # Handle check / uncheck
            if new_val and not is_checked:
                check_habit(hid, habit_date)
                st.rerun()
            elif not new_val and is_checked:
                uncheck_habit(checked_today[hid])
                st.rerun()

        st.markdown("")

    # --- 30-day history expander ---
    with st.expander("📅 View habit history (last 30 days)"):
        history_rows = fetch_habit_rows(today - timedelta(days=29), today)

        header_cols = st.columns([3] + [1] * 7)
        header_cols[0].markdown("**Habit**")
        for i, offset in enumerate(range(6, -1, -1)):
            d = today - timedelta(days=offset)
            header_cols[i + 1].markdown(f"**{d.strftime('%a')}**\n\n{d.strftime('%d')}")

        for habit in HABITS:
            row_cols = st.columns([3] + [1] * 7)
            row_cols[0].markdown(habit["label"])
            for i, offset in enumerate(range(6, -1, -1)):
                d = today - timedelta(days=offset)
                day_checked = get_checked_set(history_rows, d)
                row_cols[i + 1].markdown("✅" if habit["id"] in day_checked else "·")
