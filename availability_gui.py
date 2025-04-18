import streamlit as st  #for web applications
import pandas as pd    #classic
from datetime import datetime, timedelta   #importing date-time

#configuration for the page with title --> on the tab & page layout --> 'wide' for using the entire screen
st.set_page_config(page_title="Team Availability", layout="wide") 

st.title("🗓️ Select Your Availability")     #titile of the page
user_name = st.text_input("Enter your name:")      #taking user input

days = ["Saturday", "Sunday"]
hours = list(range(8, 21))  # 8AM to 8PM

availability = {}

for day in days:
    st.subheader(day)   #creating a sub-heading
    cols = st.columns(len(hours))   #creating columns of the length(number of columns == number of hrs -->common sense !!)
    for i, hour in enumerate(hours):
        time_str = f"{hour:02d}:00"  # Ensures 08:00, 09:00, 10:00 etc
        key = f"{user_name}_{day}_{hour}"
        available = cols[i].checkbox(time_str, key=key)  #creaitng checkboxes
        availability[f"{day} {time_str}"] = available   #available would be a bool value

#longer format
#selected_times = []
# for time, available in availability.items():
#     if available:
#         selected_times.append(time)

if st.button("✅ Submit Availability") and user_name:     
    selected_times = [time for time, available in availability.items() if available]     #.items() would return both key and value   

    if selected_times:
        df = pd.DataFrame({
            "name": [user_name] * len(selected_times),   #repeating the name multiple times i.e if one person chooses multiple times right they need to be accommodated
            "time": selected_times
        })
        df.to_csv("availability_submissions.csv", mode='a', header=not pd.io.common.file_exists("availability_submissions.csv"), index=False)
        st.success("✅ Your availability has been recorded!")
        st.write("Your selected time slots:")
        st.dataframe(df)
    else:
        st.warning("⚠️ Please select at least one time slot before submitting.")

