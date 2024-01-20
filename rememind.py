import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import pytz

from config import DISCORD_TOKEN

TOKEN = DISCORD_TOKEN
my_timezone = "America/New_York"

bot = commands.Bot(command_prefix='//', intents=discord.Intents.all())
reminders = []


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    reminder_loop.start()


@tasks.loop(seconds=30)
async def reminder_loop():
    current_time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    for reminder in reminders:
        date_type, user_id, message, reminder_time = reminder

        if current_time >= reminder_time:
            user = bot.get_user(user_id)
            if user:
                await user.send(f'{message}')
            reminders.remove(reminder)


# Bot commands start here
# CREATE A TIMER REMINDER
@bot.command(name='t', help='Set a timer for a reminder: //t [s,m,h] *integer*')
async def t(ctx, time_unit: str, duration: float):
    await ctx.send("Please enter the reminder message:")
    try:
        message_response = await bot.wait_for('message', timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        reminder_message = message_response.content
    except asyncio.TimeoutError:
        await ctx.send("You took too long to enter the reminder message.")
        return

    valid_units = ['s', 'm', 'h']

    if time_unit.lower() not in valid_units:
        await ctx.send("Invalid time unit. Use 's' for seconds, 'm' for minutes, and 'h' for hours.")
        return

    multiplier = {'s': 1, 'm': 60, 'h': 3600}
    total_seconds = duration * multiplier[time_unit.lower()]

    reminder_time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp() + total_seconds

    user_id = ctx.author.id
    date_type = 'time'
    reminders.append((date_type, user_id, reminder_message, reminder_time))
    await ctx.send(f'Timer set for {duration} {time_unit}.')


# CREATE A DATED REMINDER
@bot.command(name='d', help='Set a reminder for a certain date: //d mm/dd/yyyy HH:MM')
async def d(ctx, date: str, input_time: str):
    try:
        reminder_datetime = datetime.datetime.strptime(f"{date} {input_time}", "%m/%d/%Y %H:%M")
    except ValueError:
        await ctx.send("Invalid date or time format. Please use MM/DD/YYYY HH:MM.")
        return

    user_tz = pytz.timezone(my_timezone)
    user_datetime_utc = user_tz.localize(reminder_datetime).astimezone(pytz.utc)
    current_time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

    if user_datetime_utc.timestamp() <= current_time:
        await ctx.send("Unfortunately a time machine doesn't exist just yet - I cannot make a reminder for the past.")
        return

    await ctx.send("Please enter the reminder message:")
    try:
        message_response = await bot.wait_for('message', timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        reminder_message = message_response.content
    except asyncio.TimeoutError:
        await ctx.send("You took too long to enter the reminder message.")
        return

    user_id = ctx.author.id
    date_type = 'date'

    reminders.append((date_type, user_id, reminder_message, user_datetime_utc.timestamp()))
    await ctx.send(f'Reminder set for {reminder_datetime.strftime("%m/%d/%Y %H:%M")}')


# SHOW ALL REMINDERS
@bot.command(name='s', help='Show all reminders and their times')
async def s(ctx):
    if len(reminders) == 0:
        await ctx.send('**No active reminders**')
        return

    current_time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    output_string = f'**All Reminders**:'

    # Tuple goes: date_type (string), user_id (int), reminder_message (string), reminder_datetime (time)
    user_reminders = [reminder for reminder in reminders if reminder[1] == ctx.author.id]
    sorted_reminders = sorted(user_reminders, key=lambda x: x[3] - current_time)
    for i, reminder in enumerate(sorted_reminders, 1):
        date_type, user_id, reminder_message, reminder_time = reminder
        remaining_time = reminder_time - current_time
        hour, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        output_string = f'{output_string}\n{i}. {reminder_message} : {str(int(hour)).zfill(2)}:{str(int(minutes)).zfill(2)}:{str(int(seconds)).zfill(2)}'

    await ctx.send(output_string)


# DELETE A REMINDER
@bot.command(name='dl', help='Delete a reminder')
async def dl(ctx):
    if len(reminders) == 0:
        await ctx.send('**No Active Reminders**')
        return

    current_time = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    output_string = f'**Select a Reminder to Delete:**'
    user_reminders = [reminder for reminder in reminders if reminder[1] == ctx.author.id]
    sorted_reminders = sorted(user_reminders, key=lambda x: x[3] - current_time)
    for i, reminder in enumerate(sorted_reminders, 1):
        date_type, user_id, reminder_message, reminder_time = reminder
        remaining_time = reminder_time - current_time
        hour, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        output_string = f'{output_string}\n{i}. {reminder_message}: {str(int(hour)).zfill(2)}:{str(int(minutes)).zfill(2)}:{str(int(seconds)).zfill(2)}'

    await ctx.send(output_string)

    try:
        delete_reminder = await bot.wait_for('message', timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        if not int(delete_reminder.content) or int(delete_reminder.content) < 1 or int(delete_reminder.content) > len(reminders):
            await ctx.send("Not a valid input. Input must be an integer (eg: 1) and within the list")
            return
    except asyncio.TimeoutError:
        await ctx.send("You took too long to enter the reminder message.")
        return

    deleted = sorted_reminders[(int(delete_reminder.content)) - 1]
    reminders.remove(deleted)
    await ctx.send("Reminder deleted.")

bot.run(TOKEN)
