import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from .llms import load_llm
from typing import List
from datetime import datetime, timedelta
import json
from langchain_community.tools import tool

llm = load_llm()
load_dotenv()

CALENDAR_FILE = "agents/calendar.json"

def load_calendar():
    if not os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "w") as f:
            json.dump({}, f)
    with open(CALENDAR_FILE, "r") as f:
        return json.load(f)

def save_calendar(calendar):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(calendar, f, indent=2)

def get_calendar_for_day(day: str):
    calendar = load_calendar()
    return calendar.get(day, [])

def add_meeting(day: str, start: str, end: str):
    calendar = load_calendar()
    calendar.setdefault(day, []).append((start, end))
    save_calendar(calendar)

def get_free_busy(day: str) -> List[tuple]:
    busy_times = get_calendar_for_day(day)
    available_slots = []
    all_day_start = datetime.fromisoformat(f"{day}T09:00:00")
    current = all_day_start
    for start_str, end_str in sorted(busy_times):
        busy_start = datetime.fromisoformat(start_str)
        if (busy_start - current).total_seconds() >= 1800:
            available_slots.append((current.isoformat(), busy_start.isoformat()))
        current = datetime.fromisoformat(end_str)
    end_of_day = datetime.fromisoformat(f"{day}T17:00:00")
    if (end_of_day - current).total_seconds() >= 1800:
        available_slots.append((current.isoformat(), end_of_day.isoformat()))
    return available_slots


def is_slot_available(proposed_time: str, duration_minutes: int = 30) -> bool:
    proposed_start = datetime.fromisoformat(proposed_time)
    proposed_end = proposed_start + timedelta(minutes=duration_minutes)
    day = proposed_start.date().isoformat()
    free_slots = get_free_busy(day)
    for slot_start, slot_end in free_slots:
        start = datetime.fromisoformat(slot_start)
        end = datetime.fromisoformat(slot_end)
        if start <= proposed_start and end >= proposed_end:
            return True
    return False


def find_next_available_slot(after_time: str, duration_minutes: int = 30) -> str:
    proposed_start = datetime.fromisoformat(after_time)
    for day_offset in range(0, 30):
        check_day = (proposed_start + timedelta(days=day_offset)).date().isoformat()
        free_slots = get_free_busy(check_day)
        for slot_start, slot_end in free_slots:
            start = datetime.fromisoformat(slot_start)
            end = datetime.fromisoformat(slot_end)
            if start >= proposed_start and (end - start).total_seconds() >= duration_minutes * 60:
                return start.isoformat()
    return "No slots available."


def book_meeting(time: str, duration: int) -> str:
    end_time = datetime.fromisoformat(time) + timedelta(minutes=duration)
    day = datetime.fromisoformat(time).date().isoformat()
    add_meeting(day, time, end_time.isoformat())
    return f"📅 Meeting booked at {time} for {duration} minutes."


def suggest_booking(user_input: str) -> str:
    try:
        if "|" in user_input:
            time, duration_str = user_input.split("|")
            duration = int(duration_str.strip())
        else:
            time = user_input.strip()
            duration = 30

        proposed_start = datetime.fromisoformat(time)
        hour = proposed_start.hour

        if hour < 9 or hour >= 17 or (duration > (17-hour)*60 - proposed_start.minute):
            next_slot = find_next_available_slot(time, duration)
            return (f"⏰ The boss's working hours are from 9 AM to 5 PM.\n"
                    f"Closest available time is {next_slot}.")

        if is_slot_available(time, duration):
            return book_meeting(time, duration)
        else:
            next_slot = find_next_available_slot(time, duration)
            if "No slots" in next_slot:
                return "Boss is not available. Please try another day."
            return (f"❌ Boss has another meeting at that time.\n"
                    f"📌 Nearest available time is {next_slot}.")
    except Exception:
        print("yes")
        return "❗ Invalid input. Use format like '2025-07-12T11:00:00|60' (datetime|duration)."


@tool
def tool_suggest_booking_for_boss(time: str) -> str:
    """Suggests a meeting time or returns the nearest available slot if not free."""
    return suggest_booking(time)


meeting_scheduler_agent = create_react_agent(
    model=llm,
    tools=[tool_suggest_booking_for_boss],
    prompt="""
You are a helpful AI assistant responsible for scheduling meetings with the boss.

Follow these steps:
1. Accept input like "11am on 12 July 2025" or "9am on 13 July for 1 hour".
2. If the year is not mentioned, take it as 2025. If the duration is not mentioned, take it as 30 min.
3. Convert the given time and duration to ISO format (e.g., "2025-07-12T11:00:00|60").
4. Use the `tool_suggest_booking_for_boss` tool only once with the converted time string.
5. If output you get is  Meeting booked at "time" for "duration" minutes, tell it to user and exit. Or
6. If output get is f"⏰ The boss's working hours are from 9 AM to 5 PM. Closest available time is "next_slot"., Do not book anything in this case. tell the user the same in layman format without asking any question whether to book.""",
    name="meeting_scheduler_agent"
)


if __name__ == "__main__":
    messages = executor.invoke({'messages':'Schedule a meeting on 15th of july from from 9:30 AM for 1 hour'})
    print(messages)
