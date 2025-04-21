#importing the desired libaries
#controlling the discord bot
import discord
from discord.ext import commands, tasks
#accessing the .env file
import os
#data handling --> reading sheet files
import pandas as pd
#figuring out which time slot got the most votes
from collections import Counter
#accessing date-time
from datetime import datetime, timedelta, timezone
#accessing the pickle file generated for google authentication
import pickle
#connecting to google Calendar API
from googleapiclient.discovery import build
#connecting to Google Sheets API
import gspread
from google.oauth2.service_account import Credentials
#loading secrets from the .env file
from dotenv import load_dotenv

import json

#load_dotenv is basically temporarily making the .env file available (readable) as an environment variable
load_dotenv()

#Discord Channel credentials
#as the .env as part of the environment variables now, the os.getenv can be used to get those credentials for accessing the discord sever
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

#calling the intents class from discord.py (creating an object) --> calling the default method
# === DISCORD BOT SETUP ===
intents = discord.Intents.default() #creating an object
intents.message_content = True  #turning on permission to read message content
intents.reactions = True        #turning on permission to track reactions

#passing the intents object to the bot we created using the following class (bot is the object of class Bot)
#prefix ! will be used to call the bot, and the intents object will set the permission for the bot in that channel.
bot = commands.Bot(command_prefix="!", intents=intents)    

# === GOOGLE CALENDAR SETUP ===
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

#  TEMPORARY FOR LOCAL TESTING ONLY
# with open("sheets_credentials.json", "r") as f:
#     sheets_creds_json = f.read()

# Later this line will be used for production
sheets_creds_json = os.getenv("SHEETS_CREDENTIALS_JSON")

# Parse the string into a dictionary
sheets_creds_dict = json.loads(sheets_creds_json)

# Authorize with Google Sheets
creds = Credentials.from_service_account_info(sheets_creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open the spreadsheet
spreadsheet = client.open("availability_submissions")
worksheet = spreadsheet.sheet1

# === SCHEDULE GOOGLE MEET FUNCTION ===
def schedule_google_meet(best_time, attendee_names, email_map):
    """This function will allow scheduling a google meet"""

    #Timing Logic --> can change based on the requirements of the bot 
    #splitting the input time into day and hour
    day_str, hour_str = best_time.split()
    hour = int(hour_str.split(":")[0])  #removing ':' from the hour
    weekday_map = {"Saturday": 5, "Sunday": 6}

    today = datetime.today()        #finding today's date
    days_ahead = (weekday_map[day_str] - today.weekday()) % 7     
    meeting_date = today + timedelta(days=days_ahead)
    start_datetime = meeting_date.replace(hour=hour, minute=0, second=0, microsecond=0)

    #creating a dictionary with key :'email' and value as the actual email.
    attendee_emails = [{"email": email_map[name]} for name in attendee_names if name in email_map]

    #calling the calendar service function to establish connection to the google calendar server.
    service = get_calendar_service()
    #standard library format to write event details. 
    event = {
        "summary": "Auto Meeting Scheduler Test",
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
async def on_ready():    #on_ready function means that it will be called only during an event i.e. connecting to the discord bot
    print(f"✅ Logged in as {bot.user}")
    for task in [send_gui_link, auto_schedule_meeting]:
        try:
            task.start()
        except RuntimeError:
            pass

# === TASK 1: Send GUI Link on Friday @ 6PM BST ===
@tasks.loop(minutes=1)    #decorator function which will create a loop that will run every minute.
async def send_gui_link():
    now = datetime.now(timezone.utc)
    if now.weekday() == 4 and now.hour == 17 and now.minute == 0:  # 6PM BST
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send(               #using the await function to wait for the previous task to get finished before performing this.
            "**🗓️ Please fill out your availability for this weekend!**\n"
            "👉 Submit here: https://himanshukriplani13-discord-schedular-bo-availability-gui-zkfzdn.streamlit.app\n"
            "⏳ Deadline: **Saturday 11AM**!"
        )

# === TASK 2: Schedule Meet on Saturday @ 11AM BST ===
@tasks.loop(minutes=1)          #will run the following asynchronous function every minute ( background tasks)
async def auto_schedule_meeting():
    now = datetime.now(timezone.utc) #getting the current date and time
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:  # checking if Saturday 11am has been achieved
        channel = bot.get_channel(CHANNEL_ID)         #connecting to the discord channel where we want to send the message.
        try:
            data = worksheet.get_all_records()        #reading the google sheet
            df = pd.DataFrame(data)                   #loading the data into pandas dataframe
            df.columns = df.columns.str.strip().str.lower()      #cleans the data

            #fault finding in the code !!!
            if "time" not in df.columns or "name" not in df.columns:
                await channel.send("❌ Sheet missing `name` or `time` column.")
                return

            best_time = df["time"].value_counts().idxmax()   #using the pandas library to find out the maximum value of all
            attendees = df[df["time"] == best_time]["name"].unique()      #only unique names will be considered

            # 🛠️ Replace with your actual attendees + emails
            email_map = {
                "Himanshu": "hkriplani1@sheffield.ac.uk",
            }

            #calling the google scheduling function and storing the returned values in the variables
            meeting_time, meet_link, invited = schedule_google_meet(best_time, attendees, email_map)

            #waiting for all these actions to perform before sending the meeting details on the discord channel
            await channel.send(
                f"📅 **Meeting Scheduled!**\n"
                f"🕒 Time: **{best_time}**\n"
                f"👥 Attendees: {', '.join(attendees)}\n"
                f"🔗 Google Meet: {meet_link}"
            )

            # BONUS: Clear Sheet after scheduling
            worksheet.clear()
            worksheet.append_row(["name", "time"])
            await channel.send("🧹 Cleared availability submissions for next week!")

        except Exception as e:
            await channel.send(f"⚠️ Error during scheduling: {e}")

# === MANUAL COMMAND (OPTIONAL) ===
@bot.command()    #decorator function which will only be called on command, for manual testing if all the systems are working correctly.
async def schedule(ctx):
    """Manually trigger scheduling (debug/test only)"""
    await ctx.send("📦 Running auto scheduler manually...")
    await auto_schedule_meeting()

@bot.command()     #decorator function which will only be called on command, for manual testing of sending the form
async def sendform(ctx):
    await ctx.send(
        "**🗓️ Please fill out your availability for this weekend!**\n"
        "👉 Submit here: https://himanshukriplani13-discord-schedular-bo-availability-gui-zkfzdn.streamlit.app\n"
        "⏳ Deadline: **Saturday 11AM**!"
    )

# === RUN THE BOT ===
bot.run(TOKEN)