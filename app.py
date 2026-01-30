import streamlit as st
import pandas as pd
import json
import os
import glob
import time

st.set_page_config(page_title="Scraper Manager", layout="wide")

# Configuration (Shared with API)
jobs_file = "jobs.json"
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

st.title("🕷️ Scraper Command & Control")

# --- Sidebar: Add Jobs ---
with st.sidebar:
    st.header("Dodaj Zadanie")
    new_phrase = st.text_input("Fraza (np. kebab warszawa)")
    if st.button("Dodaj do kolejki"):
        if new_phrase:
            if os.path.exists(jobs_file):
                with open(jobs_file, "r") as f:
                    try:
                        jobs = json.load(f)
                    except:
                        jobs = []
            else:
                jobs = []
            
            new_job = {
                "id": str(int(time.time() * 1000)),
                "phrase": new_phrase,
                "status": "pending",
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            jobs.append(new_job)
            
            with open(jobs_file, "w") as f:
                json.dump(jobs, f, indent=4)
            st.success(f"Dodano: {new_phrase}")
            st.rerun()

# --- Main Area: Stats & Table ---

# Load Jobs
if os.path.exists(jobs_file):
    try:
        with open(jobs_file, "r") as f:
            jobs_data = json.load(f)
    except:
        jobs_data = []
else:
    jobs_data = []

if jobs_data:
    df = pd.DataFrame(jobs_data)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    pending = len(df[df['status'] == 'pending'])
    processing = len(df[df['status'] == 'processing'])
    done = len(df[df['status'] == 'done'])
    
    col1.metric("Oczekujące", pending)
    col2.metric("W Trakcie", processing)
    col3.metric("Ukończone", done)

    st.divider()

    # Job Table
    st.subheader("Lista Zadań")
    
    # Status coloring
    def color_status(val):
        color = 'grey'
        if val == 'done': color = 'green'
        elif val == 'processing': color = 'orange'
        elif val == 'pending': color = 'blue'
        return f'color: {color}'

    st.dataframe(
        df[['phrase', 'status', 'worker', 'added_at', 'result_file']],
        use_container_width=True
    )
else:
    st.info("Brak zadań w kolejce. Dodaj coś w pasku bocznym!")

# --- Results Section ---
st.divider()
st.subheader("📂 Wyniki (Pliki JSON)")

files = glob.glob(os.path.join(results_dir, "*.json"))
files.sort(key=os.path.getmtime, reverse=True)

for file in files:
    filename = os.path.basename(file)
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.text(filename)
    with col2:
        with open(file, "rb") as f:
            st.download_button(
                label="Pobierz",
                data=f,
                file_name=filename,
                mime="application/json"
            )
