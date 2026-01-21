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

def get_schedule_embed(date_obj):
    start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date_obj.replace(hour=23, minute=59, second=59, microsecond=999)
    
    courses = myges.get_agenda(start, end)
    
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
    time(hour=1, minute=30, tzinfo=ZoneInfo("Europe/Paris")), # 6h00: Verification (Check for updates)
    time(hour=18, minute=0, tzinfo=ZoneInfo("Europe/Paris")) # 18h00: Post tomorrow's schedule
]) 
async def schedule_loop():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print("Channel not found")
        return

    # EVENING LOGIC (Post Tomorrow's Schedule) - Runs after 17:00
    # EVENING LOGIC (Post Tomorrow's Schedule) - Runs after 17:00
    if now.hour >= 17: 
        # Cleanup: Delete previous day's message if it exists
        state = load_state()
        
        # Robust cleanup: Check history for lingering "Rappel" messages not in state
        try:
            async for history_msg in channel.history(limit=20):
                if history_msg.author == bot.user and "Rappel du planning de demain" in history_msg.content:
                    await history_msg.delete()
                    print(f"Deleted lingering text message: {history_msg.id}")
        except Exception as e:
            print(f"Error checking history for cleanup: {e}")

        if state:
            if state.get('message_id'):
                try:
                    old_msg = await channel.fetch_message(state['message_id'])
                    await old_msg.delete()
                    print("Deleted previous day's schedule message.")
                except discord.NotFound:
                    print("Previous message to delete not found.")
                except Exception as e:
                    print(f"Error deleting previous message: {e}")
            
            # Additional check for ID (though history might have caught it)
            if state.get('text_message_id'):
                try:
                    old_text_msg = await channel.fetch_message(state['text_message_id'])
                    await old_text_msg.delete()
                except discord.NotFound:
                    pass # Likely deleted by history check
                except Exception as e:
                    print(f"Error deleting previous text message by ID: {e}")

        target_date = now + timedelta(days=1)
        # Get raw courses for comparison/saving
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999)
        courses = myges.get_agenda(start, end)
        
        embed = get_schedule_embed(target_date)
        text_msg = await channel.send(f"🔔 **Rappel du planning de demain :**")
        msg = await channel.send(embed=embed)
        
        # Save state for tomorrow morning's check
        # Convert courses to a serializable format (dates handling if needed, though they are likely timestamps/strings)
        save_state(target_date.strftime("%Y-%m-%d"), courses, msg.id, channel.id, text_msg.id)
        print(f"Posted & Saved schedule for {target_date.strftime('%Y-%m-%d')}")

    # MORNING LOGIC (Check Today's Schedule) - Runs before 12:00
    else:
        target_date = now
        # Fetch fresh data for today
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = target_date.replace(hour=23, minute=59, second=59, microsecond=999)
        current_courses = myges.get_agenda(start, end)
        
        state = load_state()
        
        # If we have a saved state for TODAY
        if state and state.get('date') == target_date.strftime("%Y-%m-%d"):
            saved_courses = state.get('courses', [])
            
            # Simple comparison (JSON dumping allows deep equality check ignoring order if sorted, 
            # but lists should be roughly same order. MyGES API is consistent.)
            # We strip dynamic fields that might change per request if necessary, but usually raw data is fine.
            if json.dumps(current_courses, sort_keys=True) != json.dumps(saved_courses, sort_keys=True):
                print("Schedule changed! Deleting old message and reposting.")
                
                # Delete old message
                try:
                    old_msg = await channel.fetch_message(state['message_id'])
                    await old_msg.delete()
                except discord.NotFound:
                    print("Old message not found, just posting new.")
                except Exception as e:
                    print(f"Error deleting old message: {e}")
                
                # Robust cleanup for text message
                try:
                    async for history_msg in channel.history(limit=20):
                        if history_msg.author == bot.user and "Rappel du planning de demain" in history_msg.content:
                            await history_msg.delete()
                except Exception as e:
                    print(f"Error cleaning up text message via history: {e}")

                # Delete old text message by ID (backup)
                if state.get('text_message_id'):
                    try:
                        old_text_msg = await channel.fetch_message(state['text_message_id'])
                        await old_text_msg.delete()
                    except discord.NotFound:
                        pass
                    except Exception as e:
                        print(f"Error deleting old text message: {e}")

                # Post New
                embed = get_schedule_embed(target_date)
                text_msg = await channel.send(f"🔔 **Mise à jour du planning d'aujourd'hui :** (Changement détecté)")
                msg = await channel.send(embed=embed)
                
                # Update state (saving the new text message ID too if we want to track the update message? 
                # Actually, the user specifically mentioned "Rappel du planning". 
                # The "Mise à jour" message is different. 
                # We should probably clear the "Rappel" message if it exists, and post the "Mise à jour".
                # The code above deletes "Rappel" via history. 
                # We'll save the new IDs.
                save_state(target_date.strftime("%Y-%m-%d"), current_courses, msg.id, channel.id, text_msg.id)
            else:
                print("Schedule identical to yesterday's check. No update needed.")
        else:
             print("No state found for today or date mismatch. Doing nothing (or could post if desired).")

@schedule_loop.before_loop
async def before_schedule_loop():
    await bot.wait_until_ready()

bot.run(DISCORD_TOKEN)
