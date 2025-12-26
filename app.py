import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client
import matplotlib.pyplot as plt

# ----------------------------
# Config
# ----------------------------
st.set_page_config(
    page_title="Daily Intent Journal",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; }
    button { width: 100%; height: 3rem; }
    textarea, input { font-size: 1rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Supabase Client
# ----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TODAY = date.today()

# ----------------------------
# Helpers
# ----------------------------
def mood_to_score(mood):
    return {"😞": 1, "😐": 3, "😊": 5}.get(mood, 3)

def get_entry(d):
    res = (
        supabase.table("journal_entries")
        .select("*")
        .eq("entry_date", str(d))
        .execute()
    )
    if res.data:
        return res.data[0]

    return {
        "entry_date": str(d),
        "intentions": ["", "", ""],
        "morning_mood": "😐",
        "reflection": "",
        "top_win": "",
        "evening_mood": "",
        "evening_completed": False
    }

def upsert_entry(entry):
    supabase.table("journal_entries").upsert(entry).execute()

# ----------------------------
# Load Today
# ----------------------------
entry = get_entry(TODAY)

st.title("📝 Daily Intent Journal")

# ----------------------------
# Streak & Consistency
# ----------------------------
st.subheader("🔥 Consistency")

res = supabase.table("journal_entries").select("entry_date").eq("evening_completed", True).execute()
completed_dates = sorted([date.fromisoformat(r["entry_date"]) for r in res.data])

current_streak = 0
longest_streak = 0
temp_streak = 0
prev = None

for d in completed_dates:
    if prev and d == prev + timedelta(days=1):
        temp_streak += 1
    else:
        temp_streak = 1
    longest_streak = max(longest_streak, temp_streak)
    prev = d

if completed_dates and completed_dates[-1] == TODAY:
    current_streak = temp_streak

last_7 = [TODAY - timedelta(days=i) for i in range(7)]
consistency_7 = sum(1 for d in completed_dates if d in last_7)

st.metric("Current Streak", f"{current_streak} 🔥")
st.metric("Best Streak", f"{longest_streak} ⭐")
st.metric("Last 7 Days", f"{consistency_7}/7 ✅")

# ----------------------------
# Morning
# ----------------------------
st.divider()
st.header("🌅 Morning Intentions")

intentions = []
for i in range(3):
    intentions.append(
        st.text_input(f"Intention {i+1}", entry["intentions"][i])
    )

morning_mood = st.radio(
    "Morning Mood",
    ["😞", "😐", "😊"],
    horizontal=True,
    index=["😞", "😐", "😊"].index(entry["morning_mood"])
)

if st.button("Save Morning"):
    entry["intentions"] = intentions
    entry["morning_mood"] = morning_mood
    upsert_entry(entry)
    st.success("Morning saved")

# ----------------------------
# Evening
# ----------------------------
st.divider()
st.header("🌙 Evening Reflection")

reflection = st.text_area(
    "What worked / didn’t?",
    entry["reflection"],
    height=120
)

top_win = st.text_input(
    "🏆 Top 1 Win",
    entry["top_win"]
)

evening_mood = st.radio(
    "Evening Mood",
    ["😞", "😐", "😊"],
    horizontal=True,
    index=["😞", "😐", "😊"].index(entry["evening_mood"])
    if entry["evening_mood"] else 1
)

if st.button("Save Evening"):
    entry["reflection"] = reflection.strip()
    entry["top_win"] = top_win.strip()
    entry["evening_mood"] = evening_mood
    entry["evening_completed"] = True
    upsert_entry(entry)
    st.success("Evening saved")

# ----------------------------
# Weekly Mood Trend
# ----------------------------
st.divider()
st.header("📊 Weekly Mood Trend")

res = (
    supabase.table("journal_entries")
    .select("*")
    .eq("evening_completed", True)
    .execute()
)

if res.data:
    df = pd.DataFrame(res.data)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df = df.sort_values("entry_date").tail(7)

    df["Morning"] = df["morning_mood"].apply(mood_to_score)
    df["Evening"] = df["evening_mood"].apply(mood_to_score)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(df["entry_date"], df["Morning"], marker="o", label="Morning")
    ax.plot(df["entry_date"], df["Evening"], marker="o", label="Evening")

    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 3, 5])
    ax.set_yticklabels(["Low", "Neutral", "Good"])
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    st.pyplot(fig)
else:
    st.info("Complete at least one evening reflection to see trends.")
