
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import random
import datetime

st.set_page_config(page_title="Illinois Pick 3 Fireball Tracker", layout="centered")
st.title("🔥 Illinois Pick 3 Fireball Tracker")

# 1. Session Storage of Draw History
if "draw_history" not in st.session_state:
    st.session_state.draw_history = pd.DataFrame(columns=["date", "main", "fireball"])

# 2. Manual entry & CSV upload
with st.expander("➕ Add a Draw"):
    date = st.date_input("Date", datetime.date.today())
    main = st.text_input("Main 3‑digit (e.g., 278)")
    fireball = st.text_input("Fireball (0–9)")
    if st.button("Add Draw"):
        if len(main) == 3 and fireball.isdigit() and len(fireball) == 1:
            st.session_state.draw_history = pd.concat([
                st.session_state.draw_history,
                pd.DataFrame([{"date": str(date), "main": main, "fireball": fireball}])
            ], ignore_index=True)
            st.success("Draw added!")
        else:
            st.error("Invalid input — try again.")

uploaded = st.file_uploader("Upload CSV (columns: date, main, fireball)", type="csv")
if uploaded:
    df_u = pd.read_csv(uploaded)
    st.session_state.draw_history = pd.concat([st.session_state.draw_history, df_u], ignore_index=True)
    st.success("CSV data added!")

# 3. Auto-fetching from Lottery Post
def fetch_latest_draw():
    url = "https://www.lotterypost.com/results/il"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Look for the Pick 3 Evening section
    section = soup.find("div", string="Pick 3 Evening")
    if not section:
        return None

    parent = section.find_parent("div")
    nums = parent.select("ul > li")[1:4]  # main digits
    fb = parent.select("ul > li")[4].text.strip()  # Fireball

    # Get draw date
    date = parent.find_previous("h2").get_text(strip=True)
    main = "".join(li.text.strip() for li in nums)
    return {"date": date, "main": main, "fireball": fb}

if st.button("🔄 Auto‑Fetch Latest Draw"):
    res = fetch_latest_draw()
    if res:
        st.session_state.draw_history = pd.concat([
            st.session_state.draw_history,
            pd.DataFrame([res])
        ], ignore_index=True)
        st.success(f"Fetched {res['main']} (Fireball {res['fireball']}) on {res['date']}")
    else:
        st.error("Fetch failed. Site layout may have changed.")

# 4. Display history
st.dataframe(st.session_state.draw_history.tail(10), use_container_width=True)

# 5. Frequency Analysis & Suggestions
if not st.session_state.draw_history.empty:
    all_main = [int(d) for row in st.session_state.draw_history["main"] for d in row]
    main_freq = Counter(all_main)
    fire_freq = Counter(map(int, st.session_state.draw_history["fireball"]))

    df_main = pd.DataFrame(main_freq.items(), columns=["Digit", "Main Freq"]).set_index("Digit")
    df_fire = pd.DataFrame(fire_freq.items(), columns=["Digit", "Fireball Freq"]).set_index("Digit")

    st.bar_chart(df_main)
    st.bar_chart(df_fire)

    hot_main = [d for d, _ in main_freq.most_common(3)]
    cold_main = [d for d, _ in main_freq.most_common()[-3:]]
    hot_fire = [d for d, _ in fire_freq.most_common(3)]

    def gen(nlist, flist):
        combos = []
        for _ in range(5):
            combos.append(("".join(str(random.choice(nlist)) for _ in range(3)),
                           str(random.choice(flist))))
        return combos

    hot = gen(hot_main, hot_fire)
    cold = gen(cold_main, hot_fire)
    df_sug = pd.DataFrame({
        "🔥Hot Combinations": [f"{m} (FB: {f})" for m, f in hot],
        "❄️Cold Combinations": [f"{m} (FB: {f})" for m, f in cold],
    })
    st.dataframe(df_sug, use_container_width=True)
else:
    st.info("Add or fetch at least one draw to begin.")
