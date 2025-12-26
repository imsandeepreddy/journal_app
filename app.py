import streamlit as st
import pandas as pd
import json
from datetime import date
import matplotlib.pyplot as plt
from fpdf import FPDF

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

entry = data.get(today, {
    "intentions": ["", "", ""],
    "morning_mood": "😐",
    "reflection": "",
    "top_win": "",
    "evening_mood": "😐"
})

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

# ----------------------------
# Evening Section
# ----------------------------
st.header("🌙 Evening Reflection")

reflection = st.text_area("What worked / didn’t work today?", entry["reflection"])
top_win = st.text_input("🏆 Top 1 Win of the Day", entry["top_win"])

evening_mood = st.radio(
    "Evening Mood",
    ["😞", "😐", "😊"],
    horizontal=True,
    index=["😞", "😐", "😊"].index(entry["evening_mood"])
)

# ----------------------------
# Save Entry
# ----------------------------
if st.button("💾 Save Journal Entry"):
    data[today] = {
        "intentions": intentions,
        "morning_mood": morning_mood,
        "reflection": reflection,
        "top_win": top_win,
        "evening_mood": evening_mood
    }
    save_data(data)
    st.success("Entry saved")

# ----------------------------
# Weekly Summary
# ----------------------------
st.header("📊 Weekly Summary")

if data:
    df = []
    for d, v in data.items():
        df.append({
            "date": d,
            "morning": mood_to_score(v["morning_mood"]),
            "evening": mood_to_score(v["evening_mood"])
        })

    df = pd.DataFrame(df)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(7)

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["morning"], label="Morning Mood")
    ax.plot(df["date"], df["evening"], label="Evening Mood")
    ax.set_ylim(0, 6)
    ax.legend()
    st.pyplot(fig)

# ----------------------------
# Export Section
# ----------------------------
st.header("📤 Export")

def export_markdown():
    md = "# Daily Journal\n\n"
    for d, v in data.items():
        md += f"## {d}\n"
        md += f"- Intentions: {', '.join(v['intentions'])}\n"
        md += f"- Top Win: {v['top_win']}\n"
        md += f"- Reflection: {v['reflection']}\n"
        md += f"- Mood: {v['morning_mood']} → {v['evening_mood']}\n\n"
    return md

def export_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for d, v in data.items():
        pdf.multi_cell(0, 8, f"{d}\nIntentions: {', '.join(v['intentions'])}\n"
                            f"Top Win: {v['top_win']}\n"
                            f"Reflection: {v['reflection']}\n"
                            f"Mood: {v['morning_mood']} → {v['evening_mood']}\n\n")
    path = "/tmp/journal.pdf"
    pdf.output(path)
    return path

st.download_button(
    "⬇️ Export Markdown",
    export_markdown(),
    file_name="journal.md"
)

pdf_path = export_pdf()
with open(pdf_path, "rb") as f:
    st.download_button(
        "⬇️ Export PDF",
        f,
        file_name="journal.pdf"
    )
