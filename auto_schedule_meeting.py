import pandas as pd
from datetime import datetime, timedelta
import pickle
from googleapiclient.discovery import build

# ----------- STEP 1: Load availability ----------
df = pd.read_csv("availability_submissions.csv")

# Clean headers
df.columns = df.columns.str.strip().str.lower()

# Count time votes
best_time = df["time"].value_counts().idxmax()

# Filter attendees for that time
attendees = df[df["time"] == best_time]["name"].unique()

# Dummy email map (replace with real ones later!)
email_map = {
    "Himanshu": "hkriplani1@sheffield.ac.uk",
}

attendee_emails = [ {"email": email_map[name]} for name in attendees if name in email_map ] 

# ----------- STEP 2: Parse datetime ----------
day_str, hour_str = best_time.split()  # e.g. "Sunday 10:00"
hour = int(hour_str.split(":")[0])

# Set event datetime
today = datetime.today()
weekday_map = {"Saturday": 5, "Sunday": 6}
days_ahead = (weekday_map[day_str] - today.weekday()) % 7
meeting_date = today + timedelta(days=days_ahead)
start_datetime = meeting_date.replace(hour=hour, minute=0, second=0, microsecond=0)

# ----------- STEP 3: Auth with Google Calendar ----------
def get_calendar_service():
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)
    return build("calendar", "v3", credentials=creds)

service = get_calendar_service()

event = {
    "summary": "Team Weekly Sync",
    "start": {
        "dateTime": start_datetime.isoformat(),
        "timeZone": "Europe/London",
    },
    "end": {
        "dateTime": (start_datetime + timedelta(hours=1)).isoformat(),
        "timeZone": "Europe/London",
    },
    "attendees": attendee_emails,
    "conferenceData": {
        "createRequest": {
            "requestId": f"meet-{start_datetime.timestamp()}",
            "conferenceSolutionKey": {"type": "hangoutsMeet"},
        }
    },
}

event = service.events().insert(
    calendarId="primary",
    body=event,
    sendUpdates="all",
    conferenceDataVersion=1
).execute()

# ----------- DONE! -----------
print("✅ Google Meet created for:", best_time)
print("🔗 Meet link:", event.get("hangoutLink"))
print("📧 Invited:", attendee_emails)
