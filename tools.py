import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from ics import Calendar, Event
import json
import pytz
from typing import Optional
import random

COMPLETION_PHRASES = [
    "Task completed.", "Done, Sir.", "It is finished.", "Job done.", "All set."
]

def classy_done():
    return random.choice(COMPLETION_PHRASES)

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            return f"{response.text.strip()}. {classy_done()}"
        else:
            return f"Could not retrieve weather for {city}. Shall I try again?"
    except Exception:
        return "An error occurred while retrieving weather. Shall I try again?"

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        return f"{results} {classy_done()}"
    except Exception:
        return "An error occurred while searching the web. Shall I try again?"

@function_tool()
async def calculate(context: RunContext, expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"The result is {result}. {classy_done()}"
    except Exception:
        return "Error in calculation. Shall I try again?"

@function_tool()
async def get_current_time(context: RunContext, timezone: Optional[str] = "Africa/Lagos") -> str:
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"The current time in {timezone} is {now}. {classy_done()}"
    except Exception:
        return "Couldn't get the time. Shall I try again?"

@function_tool()
async def book_appointment(context: RunContext, title: str, date: str, time: str, duration_minutes: int = 30) -> str:
    try:
        start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=duration_minutes)
        event = Event(name=title, begin=start, end=end)
        calendar = Calendar(events=[event])
        with open("appointments.ics", "a") as f:
            f.writelines(calendar.serialize_iter())
        return f"Appointment '{title}' booked on {date} at {time}. {classy_done()}"
    except Exception:
        return "Failed to book appointment. Shall I try again?"

@function_tool()
async def list_appointments(context: RunContext) -> str:
    try:
        if not os.path.exists("appointments.ics"):
            return "No appointments found."
        with open("appointments.ics", "r") as f:
            calendar = Calendar(f.read())
        now = datetime.now()
        events = [f"{e.name} on {e.begin.format('YYYY-MM-DD')} at {e.begin.format('HH:mm')}" for e in calendar.events if e.begin.datetime >= now]
        return "Your upcoming appointments:\n" + "\n".join(events) + f"\n{classy_done()}" if events else "No upcoming appointments."
    except Exception:
        return "Failed to list appointments. Shall I try again?"

@function_tool()
async def delete_appointment(context: RunContext, title: str, date: str) -> str:
    try:
        if not os.path.exists("appointments.ics"):
            return "No appointments found to delete."
        with open("appointments.ics", "r") as f:
            calendar = Calendar(f.read())
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        updated, deleted = [], False
        for event in calendar.events:
            if event.name.lower() == title.lower() and event.begin.date() == target_date:
                deleted = True
                continue
            updated.append(event)
        if not deleted:
            return f"No appointment titled '{title}' on {date} was found."
        with open("appointments.ics", "w") as f:
            f.writelines(Calendar(events=updated).serialize_iter())
        return f"Deleted appointment '{title}' on {date}. {classy_done()}"
    except Exception:
        return "Error deleting appointment. Shall I try again?"

TODO_FILE = "todo.json"

def load_tasks():
    if not os.path.exists(TODO_FILE): return []
    with open(TODO_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TODO_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

@function_tool()
async def add_task(context: RunContext, task: str) -> str:
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return f"The task '{task}' has been added. {classy_done()}"

@function_tool()
async def list_tasks(context: RunContext) -> str:
    tasks = load_tasks()
    if not tasks:
        return "Your to-do list is empty."
    return "Your tasks:\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks)) + f"\n{classy_done()}"

@function_tool()
async def remove_task(context: RunContext, task_number: int) -> str:
    tasks = load_tasks()
    try:
        removed = tasks.pop(task_number - 1)
        save_tasks(tasks)
        return f"Removed task: '{removed}'. {classy_done()}"
    except IndexError:
        return "Invalid task number. Shall I try again?"

@function_tool()
async def send_email(context: RunContext, to_email: str, subject: str, message: str, cc_email: Optional[str] = None) -> str:
    try:
        smtp_server, smtp_port = "smtp.gmail.com", 587
        user, password = os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD")
        if not user or not password:
            return "Gmail credentials are not set."
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = user, to_email, subject
        recipients = [to_email] + ([cc_email] if cc_email else [])
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
        server.quit()
        return f"Email sent successfully to {to_email}. {classy_done()}"
    except smtplib.SMTPAuthenticationError:
        return "Authentication failed. Check Gmail app password."
    except smtplib.SMTPException:
        return "SMTP error occurred."
    except Exception:
        return "An error occurred while sending the email. Shall I try again?"
