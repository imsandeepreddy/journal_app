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

# Default structure per day
if today not in data:
    data[today] = {
        "intentions": ["", "", ""],
        "morning_mood": "😐",
        "reflection": "",
        "top_win": "",
        "evening_mood": ""
    }

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
    data[today]["reflection"] = reflection
    data[today]["top_win"] = top_win
    data[today]["evening_mood"] = evening_mood
    save_data(data)
    st.success("Evening reflection saved")

# ----------------------------
# Weekly Summary (Only Completed Days)
# ----------------------------
st.header("📊 Weekly Summary (Completed Days Only)")

completed_rows = []

for d, v in data.items():
    if v["evening_mood"] and v["reflection"]:
        completed_rows.append({
            "date": d,
            "morning": mood_to_score(v["morning_mood"]),
            "evening": mood_to_score(v["evening_mood"])
        })

if completed_rows:
    df = pd.DataFrame(completed_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(7)

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["morning"], label="Morning Mood")
    ax.plot(df["date"], df["evening"], label="Evening Mood")
    ax.set_ylim(0, 6)
    ax.legend()
    st.pyplot(fig)
else:
    st.info("Weekly summary will appear once evening reflections are saved.")
