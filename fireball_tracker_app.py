
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import random
import datetime

st.set_page_config(page_title="Illinois Pick 3 Fireball Tracker", layout="centered")

st.title("🔥 Illinois Pick 3 Fireball Tracker")

# --- 1. Load or Input Draw Data ---
st.subheader("📥 Input or Fetch Draw History")

# Session state for history
if "draw_history" not in st.session_state:
    st.session_state.draw_history = pd.DataFrame(columns=["date", "main", "fireball"])

# Manual entry
with st.expander("➕ Manually Add a Draw"):
    date = st.date_input("Draw Date", datetime.date.today())
    main = st.text_input("Main Pick 3 (e.g., 278)")
    fireball = st.text_input("Fireball (0-9)")

    if st.button("Add Draw"):
        if len(main) == 3 and fireball.isdigit() and len(fireball) == 1:
            st.session_state.draw_history = pd.concat([
                st.session_state.draw_history,
                pd.DataFrame([{"date": date, "main": main, "fireball": fireball}])
            ], ignore_index=True)
            st.success("Draw added!")
        else:
            st.error("Please enter a valid 3-digit main number and 1-digit Fireball.")

# Upload CSV
uploaded = st.file_uploader("Or upload a CSV file with columns: date, main, fireball")
if uploaded:
    df_uploaded = pd.read_csv(uploaded)
    st.session_state.draw_history = pd.concat([st.session_state.draw_history, df_uploaded], ignore_index=True)
    st.success("CSV uploaded!")

# Auto-fetch from Illinois Lottery site
def fetch_latest_draw():
    try:
        url = "https://www.illinoislottery.com/dbg/results/pick-3"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        draw_section = soup.find("div", class_="number-list")
        draw_numbers = draw_section.find_all("span", class_="number")
        fireball = soup.find("span", class_="fireball-number").text.strip()
        numbers = [d.text.strip() for d in draw_numbers[:3]]
        main_draw = ''.join(numbers)
        draw_date = datetime.date.today()
        return {"date": draw_date, "main": main_draw, "fireball": fireball}
    except:
        return None

if st.button("🔄 Auto-Fetch Latest Draw"):
    result = fetch_latest_draw()
    if result:
        st.session_state.draw_history = pd.concat([
            st.session_state.draw_history,
            pd.DataFrame([result])
        ], ignore_index=True)
        st.success(f"Fetched and added draw: {result['main']} Fireball: {result['fireball']}")
    else:
        st.error("Could not fetch draw. Website structure may have changed.")

# Display current draw history
st.dataframe(st.session_state.draw_history.tail(10), use_container_width=True)

# --- 2. Frequency Analysis ---
st.subheader("📊 Frequency Analysis")

if not st.session_state.draw_history.empty:
    all_main_digits = [int(d) for num in st.session_state.draw_history["main"] for d in num]
    main_freq = Counter(all_main_digits)
    fire_freq = Counter(map(int, st.session_state.draw_history["fireball"]))

    df_main = pd.DataFrame(main_freq.items(), columns=["Digit", "Main Frequency"]).sort_values(by="Main Frequency", ascending=False)
    df_fire = pd.DataFrame(fire_freq.items(), columns=["Digit", "Fireball Frequency"]).sort_values(by="Fireball Frequency", ascending=False)

    st.write("**Main Digit Frequency**")
    st.bar_chart(df_main.set_index("Digit"))

    st.write("**Fireball Digit Frequency**")
    st.bar_chart(df_fire.set_index("Digit"))

    hot_main = [d for d, _ in main_freq.most_common(3)]
    cold_main = [d for d, _ in main_freq.most_common()[-3:]]
    hot_fire = [d for d, _ in fire_freq.most_common(3)]
    cold_fire = [d for d, _ in fire_freq.most_common()[-3:]]

    # --- 3. Suggested Combinations ---
    st.subheader("🎯 Suggested Combinations")

    def gen_combos(main_digits, fire_digits, n=5):
        combos = []
        for _ in range(n):
            m = ''.join(str(random.choice(main_digits)) for _ in range(3))
            f = str(random.choice(fire_digits))
            combos.append((m, f))
        return combos

    hot_combos = gen_combos(hot_main, hot_fire)
    cold_combos = gen_combos(cold_main, hot_fire)

    df_suggestions = pd.DataFrame({
        "🔥 Hot Combos": [f"{m} (FB: {f})" for m, f in hot_combos],
        "❄️ Cold Combos": [f"{m} (FB: {f})" for m, f in cold_combos]
    })
    st.dataframe(df_suggestions, use_container_width=True)
else:
    st.info("Please add or fetch draw data to begin analysis.")
