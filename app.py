import streamlit as st
import pandas as pd
import json
from datetime import date
import matplotlib.pyplot as plt

DATA_FILE = "journal_data.json"

# ----------------------------
# Utility Functions
# ----------------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def mood_to_score(mood):
    return {"😞": 1, "😐": 3, "😊": 5}.get(mood, 3)

# ----------------------------
# App Config
# ----------------------------
st.set_page_config(page_title="Daily Intent & Reflection", layout="centered")
st.title("📝 Daily Intent & Reflection Journal")

data = load_data()
today = str(date.today())

# ----------------------------
# Default Day Structure (Backward Safe)
# ----------------------------
if today not in data:
    data[today] = {}

data[today].setdefault("intentions", ["", "", ""])
data[today].setdefault("morning_mood", "😐")
data[today].setdefault("reflection", "")
data[today].setdefault("top_win", "")
data[today].setdefault("evening_mood", "")
data[today].setdefault("evening_completed", False)

entry = data[today]

# ----------------------------
# Morning Section
# ----------------------------
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

if st.button("💾 Save Morning Intentions"):
    data[today]["intentions"] = intentions
    data[today]["morning_mood"] = morning_mood
    save_data(data)
    st.success("Morning intentions saved")

# ----------------------------
# Evening Section
# ----------------------------
st.header("🌙 Evening Reflection")

reflection = st.text_area(
    "What worked / didn’t work today?",
    entry["reflection"]
)

top_win = st.text_input(
    "🏆 Top 1 Win of the Day",
    entry["top_win"]
)

evening_mood = st.radio(
    "Evening Mood",
    ["😞", "😐", "😊"],
    horizontal=True,
    index=["😞", "😐", "😊"].index(entry["evening_mood"])
    if entry["evening_mood"] else 1
)

if st.button("💾 Save Evening Reflection"):
    data[today]["reflection"] = reflection.strip()
    data[today]["top_win"] = top_win.strip()
    data[today]["evening_mood"] = evening_mood
    data[today]["evening_completed"] = True
    save_data(data)
    st.success("Evening reflection saved")

# ----------------------------
# Weekly Summary (Completed Days Only)
# ----------------------------
st.header("📊 Weekly Mood Trend (Completed Days)")

rows = []

for d, v in data.items():
    if v.get("evening_completed"):
        rows.append({
            "date": d,
            "Morning Mood": mood_to_score(v.get("morning_mood")),
            "Evening Mood": mood_to_score(v.get("evening_mood"))
        })

if rows:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(7)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(
        df["date"],
        df["Morning Mood"],
        marker="o",
        linewidth=2,
        label="Morning"
    )

    ax.plot(
        df["date"],
        df["Evening Mood"],
        marker="o",
        linewidth=2,
        label="Evening"
    )

    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 3, 5])
    ax.set_yticklabels(["Low", "Neutral", "Good"])

    ax.set_xlabel("Date")
    ax.set_ylabel("Mood Level")
    ax.set_title("Mood Change Across the Day")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)

    st.pyplot(fig)
else:
    st.info("Complete at least one evening reflection to see trends.")
