import discord
from discord.ext import commands, tasks
import os
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta, timezone
import pickle
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

#Discord Channel credentials
# --- DIRECTLY HARDCODED VALUES ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === GOOGLE CALENDAR SETUP ===
def get_calendar_service():
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)
    return build("calendar", "v3", credentials=creds)

def schedule_google_meet(best_time, attendee_names, email_map):
    # Parse 'Saturday 08:00'
    day_str, hour_str = best_time.split()
    hour = int(hour_str.split(":")[0])
    weekday_map = {"Saturday": 5, "Sunday": 6}

    today = datetime.today()
    days_ahead = (weekday_map[day_str] - today.weekday()) % 7
    meeting_date = today + timedelta(days=days_ahead)
    start_datetime = meeting_date.replace(hour=hour, minute=0, second=0, microsecond=0)

    attendee_emails = [{"email": email_map[name]} for name in attendee_names if name in email_map]

    service = get_calendar_service()
    event = {
        "summary": "Team Sync (Auto Scheduled)",
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
                "requestId": f"discord-scheduler-{start_datetime.timestamp()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    event = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event,
        sendUpdates="all",
        conferenceDataVersion=1
    ).execute()

    return start_datetime, event.get("hangoutLink"), attendee_emails

# === DISCORD EVENTS ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    for task in [send_gui_link, auto_schedule_meeting]:
        try:
            task.start()
        except RuntimeError:
            pass

# === TASK 1: Send GUI Link on Friday @ 6PM BST ===
@tasks.loop(minutes=1)
async def send_gui_link():
    now = datetime.now(timezone.utc)
    if now.weekday() == 4 and now.hour == 17 and now.minute == 0:  # 6PM BST
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send(
            "**🗓️ Please fill out your availability for this weekend!**\n"
            "👉 Submit here: http://192.168.0.36:8501\n"
            "⏳ Deadline: **Saturday 11AM**!"
        )

# === TASK 2: Schedule Meet on Saturday @ 11AM BST ===
@tasks.loop(minutes=1)
async def auto_schedule_meeting():
    now = datetime.now(timezone.utc)
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:  # 11AM BST
        channel = bot.get_channel(CHANNEL_ID)
        try:
            df = pd.read_csv("availability_submissions.csv")
            df.columns = df.columns.str.strip().str.lower()

            if "time" not in df.columns or "name" not in df.columns:
                await channel.send("❌ CSV missing `name` or `time` column.")
                return

            best_time = df["time"].value_counts().idxmax()
            attendees = df[df["time"] == best_time]["name"].unique()

            # 🛠️ Replace with your actual attendees + emails
            email_map = {
                "Himanshu": "hkriplani1@sheffield.ac.uk",
            }

            meeting_time, meet_link, invited = schedule_google_meet(best_time, attendees, email_map)

            await channel.send(
                f"📅 **Meeting Scheduled!**\n"
                f"🕒 Time: **{best_time}**\n"
                f"👥 Attendees: {', '.join(attendees)}\n"
                f"🔗 Google Meet: {meet_link}"
            )

            # BONUS: Clear CSV after scheduling
            open("availability_submissions.csv", "w").close()
            await channel.send("🧹 Cleared availability submissions for next week!")

        except Exception as e:
            await channel.send(f"⚠️ Error during scheduling: {e}")

# === MANUAL COMMAND (OPTIONAL) ===
@bot.command()
async def schedule(ctx):
    """Manually trigger scheduling (debug/test only)"""
    await ctx.send("📦 Running auto scheduler manually...")
    await auto_schedule_meeting()


@bot.command()
async def sendform(ctx):
    await ctx.send(
        "**🗓️ Please fill out your availability for this weekend!**\n"
        "👉 Submit here: http://localhost:8501\n"
        "⏳ Deadline: **Saturday 11AM**!"
    )


# === RUN THE BOT ===
bot.run(TOKEN)
