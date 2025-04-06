import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Team Availability", layout="wide")

st.title("🗓️ Select Your Availability")
user_name = st.text_input("Enter your name:")

days = ["Saturday", "Sunday"]
hours = list(range(8, 21))  # 8AM to 8PM

availability = {}

for day in days:
    st.subheader(day)
    cols = st.columns(len(hours))
    for i, hour in enumerate(hours):
        time_str = f"{hour:02d}:00"  # Ensures 08:00, 09:00, 10:00 etc
        key = f"{user_name}_{day}_{hour}"
        available = cols[i].checkbox(time_str, key=key)
        availability[f"{day} {time_str}"] = available

if st.button("✅ Submit Availability") and user_name:
    selected_times = [time for time, available in availability.items() if available]

    if selected_times:
        df = pd.DataFrame({
            "name": [user_name] * len(selected_times),
            "time": selected_times
        })
        df.to_csv("availability_submissions.csv", mode='a', header=not pd.io.common.file_exists("availability_submissions.csv"), index=False)
        st.success("✅ Your availability has been recorded!")
        st.write("Your selected time slots:")
        st.dataframe(df)
    else:
        st.warning("⚠️ Please select at least one time slot before submitting.")

