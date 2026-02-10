import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from bs4 import BeautifulSoup
from myges_utils import MyGESClient
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, time
import asyncio
import json

load_dotenv()

STATE_FILE = "schedule_state.json"

def save_state(date_str, courses, message_id, channel_id, text_message_id=None):
    state = {
        "date": date_str,
        "courses": courses,
        "message_id": message_id,
        "channel_id": channel_id,
        "text_message_id": text_message_id
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

MYGES_EMAIL = os.getenv("MYGES_EMAIL")
MYGES_PASSWORD = os.getenv("MYGES_PASSWORD")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Initialize MyGES Client
myges = MyGESClient(MYGES_EMAIL, MYGES_PASSWORD)

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def filter_courses(raw_courses):
    filtered = []
    for course in raw_courses:
        teacher = course.get('discipline', {}).get('teacher', 'N/A')
        course_type = course.get('type', 'N/A')
        
        # Criteria 1: Must have a teacher (not None, not 'N/A', not empty)
        if not teacher or teacher == 'N/A':
            continue
            
        # Criteria 2: Must not be "Libre" (unimportant)
        if course_type == "Libre":
            continue
            
        filtered.append(course)
    return filtered

def get_schedule_embed(date_obj):
    start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date_obj.replace(hour=23, minute=59, second=59, microsecond=999)
    
    raw_courses = myges.get_agenda(start, end)
    courses = filter_courses(raw_courses)
    
    locale_date = date_obj.strftime("%d/%m/%Y")
    # MyGES Red Color: 0xE0020B
    embed = discord.Embed(title=f"📅  {locale_date}", color=0xE0020B)
    embed.set_author(name="MyGES Planning", icon_url="https://www.myges.fr/assets/img/logo_myges.png")
    
    if not courses:
        embed.description = "🏖️ **Aucun cours prévu !** Profite de ta journée."
        return embed

    # Sort courses by start date
    courses.sort(key=lambda x: x.get('start_date', 0))

    for course in courses:
        name = course.get('name', 'N/A')
        start_ts = course.get('start_date', 0) // 1000
        end_ts = course.get('end_date', 0) // 1000
        
        rooms_list = course.get('rooms') or []
        rooms = ", ".join([r.get('name', '?') for r in rooms_list])
        campus = ", ".join(list(set([r.get('campus', '?') for r in rooms_list])))
        teacher = course.get('discipline', {}).get('teacher', 'N/A')
        modality = course.get('modality', 'N/A')
        course_type = course.get('type', 'N/A')
        
        # Native Discord Timestamp formatting
        time_str = f"<t:{start_ts}:t> - <t:{end_ts}:t>"
        
        # Build dynamic value string
        parts = [f"> 📚 **{name}**"]
        
        if course_type == "Libre":
             parts.append("> 🗽 *Travail en autonomie*")
        else:
            if teacher and teacher != "N/A":
                parts.append(f"> 🧑‍🏫 *{teacher}*")
                
            if rooms_list:
                parts.append(f"> 🏫 `{rooms}` ({campus})")
            elif modality == "Distanciel" or "E-LEARNING" in name.upper():
                parts.append("> 🏠 *Distanciel / E-Learning*")
            
        parts.append(f"> 🏷️ {course_type} • {modality}")
        
        # Join with empty block quote lines for spacing
        value = "\n> \n".join(parts)
        
        embed.add_field(name=f"⏰ {time_str}", value=value, inline=False)
        
    embed.set_footer(text=f"Total: {len(courses)} cours")
    return embed

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not schedule_loop.is_running():
        schedule_loop.start()

@bot.command(name="agenda")
async def agenda(ctx, date_str=None):
    """
    Affiche l'emploi du temps.
    Usage: !agenda (pour demain) ou !agenda today (pour aujourd'hui)
    """
    target_date = datetime.now() + timedelta(days=1) # Default to tomorrow
    
    if date_str == "today" or date_str == "aujourdhui":
        target_date = datetime.now()
    
    embed = get_schedule_embed(target_date)
    await ctx.send(embed=embed)

@tasks.loop(time=[
    time(hour=6, minute=0, tzinfo=ZoneInfo("Europe/Paris")), # 6h00: Verification (Check for updates)
    time(hour=15, minute=53, tzinfo=ZoneInfo("Europe/Paris")),
    time(hour=18, minute=0, tzinfo=ZoneInfo("Europe/Paris")) # 18h00: Post tomorrow's schedule
]) 
async def schedule_loop():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print("Channel not found")
        return

    # EVENING LOGIC (Post Tomorrow's Schedule) - Runs after 17:00
    # EVENING LOGIC (Post Tomorrow's Schedule) - Runs after 15:00
    if now.hour >= 15: 
        # Cleanup: Delete ALL previous bot messages (Rappel/Planning) in history
        # Because file state is lost on Fly.io restart/deploy
        try:
            async for history_msg in channel.history(limit=20):
                if history_msg.author == bot.user:
                    # Check if it's a schedule message (by content or embed)
                    # We look for "Rappel", "Mise à jour", or an embed with "MyGES Planning"
                    is_schedule = False
                    if "Rappel du planning" in history_msg.content:
                        is_schedule = True
                    elif "Mise à jour du planning" in history_msg.content:
                        is_schedule = True
                    elif history_msg.embeds and "MyGES Planning" in (history_msg.embeds[0].author.name or ""):
                        is_schedule = True
                    
                    if is_schedule:
                        await history_msg.delete()
                        print(f"Deleted old schedule message: {history_msg.id}")
        except Exception as e:
            print(f"Error cleaning up history: {e}")

        target_date = now + timedelta(days=1)
        # Get raw courses
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999)
        courses = filter_courses(myges.get_agenda(start, end))
        
        if not courses:
            print(f"No courses for {target_date}, skipping message.")
            # Still save state so morning check knows we skipped (message_id=None)
            save_state(target_date.strftime("%Y-%m-%d"), courses, None, channel.id)
        else:
            embed = get_schedule_embed(target_date)
            # Send ONE message
            msg = await channel.send(content="🔔 **Rappel du planning de demain :**", embed=embed)
            
            # We still save state for the morning check
            save_state(target_date.strftime("%Y-%m-%d"), courses, msg.id, channel.id)
            print(f"Posted & Saved schedule for {target_date.strftime('%Y-%m-%d')}")

    # MORNING LOGIC (Check Today's Schedule) - Runs before 12:00
    else:
        target_date = now
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999)
        current_courses = filter_courses(myges.get_agenda(start, end))
        
        state = load_state()
        
        # Try to find recent message in history if state is lost
        last_bot_msg = None
        if not state:
            async for m in channel.history(limit=10):
                if m.author == bot.user and m.embeds and "MyGES Planning" in (m.embeds[0].author.name or ""):
                    last_bot_msg = m
                    break
        
        # Determine comparison source
        saved_courses = []
        if state and state.get('date') == target_date.strftime("%Y-%m-%d"):
            saved_courses = state.get('courses', [])
        # If no state but we found a message, we might assume it *was* correct, but we can't easily extracting courses from Embed.
        # So for morning check, strict state is better. 
        # But if state is lost, we basically can't check for DIFF, we can only Repost if we want strict consistency.
        # For now, let's keep the logic: If no state, do nothing (to avoid spamming). 
        # BUT if the user wants "Morning Update", they rely on state.
        
        if state and state.get('date') == target_date.strftime("%Y-%m-%d"):
            if json.dumps(current_courses, sort_keys=True) != json.dumps(saved_courses, sort_keys=True):
                print("Schedule changed! Deleting old message and reposting.")
                
                # Delete old message (State ID)
                try:
                    if state.get('message_id'):
                        old_msg = await channel.fetch_message(state['message_id'])
                        await old_msg.delete()
                except:
                    pass

                # Also cleanup history just in case
                async for history_msg in channel.history(limit=10):
                    if history_msg.author == bot.user and ("Rappel" in history_msg.content or "Mise à jour" in history_msg.content):
                        await history_msg.delete()

                if not current_courses:
                    print("Courses cleared. No message to send.")
                    save_state(target_date.strftime("%Y-%m-%d"), current_courses, None, channel.id)
                else: 
                    embed = get_schedule_embed(target_date)
                    msg = await channel.send(content="🔔 **Mise à jour du planning d'aujourd'hui :** (Changement détecté)", embed=embed)
                    
                    save_state(target_date.strftime("%Y-%m-%d"), current_courses, msg.id, channel.id)
            else:
                 print("No change detected.")
        else:
             print("No state found for today. Skipping update check.")

@schedule_loop.before_loop
async def before_schedule_loop():
    await bot.wait_until_ready()

bot.run(DISCORD_TOKEN)
