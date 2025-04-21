import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os
import json


# Page configuration
st.set_page_config(page_title="Team Availability", layout="wide") 

# Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
sheets_creds_json = os.getenv("SHEETS_CREDENTIALS_JSON")
sheets_creds_dict = json.loads(sheets_creds_json)

# Setup Google Sheets client
creds = Credentials.from_service_account_info(sheets_creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open your spreadsheet
spreadsheet = client.open("availability_submissions")
worksheet = spreadsheet.sheet1

days = ["Saturday", "Sunday"]
hours = list(range(8, 21))  # 8AM to 8PM

availability = {}

for day in days:
    st.subheader(day)
    cols = st.columns(len(hours))
    for i, hour in enumerate(hours):
        time_str = f"{hour:02d}:00"
        key = f"{user_name}_{day}_{hour}"
        available = cols[i].checkbox(time_str, key=key)
        availability[f"{day} {time_str}"] = available

# Submit availability
if st.button("✅ Submit Availability") and user_name:
    selected_times = [time for time, available in availability.items() if available]

    if selected_times:
        for time in selected_times:
            worksheet.append_row([user_name, time])  # Append to Google Sheet
        
        st.success("✅ Your availability has been recorded in Google Sheets!")
        st.write("Your selected time slots:")
        df = pd.DataFrame({
            "name": [user_name] * len(selected_times),
            "time": selected_times
        })
        st.dataframe(df)
    else:
        st.warning("⚠️ Please select at least one time slot before submitting.")

