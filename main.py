import discord
import requests
import random
import asyncio
import os
import openai
from discord.ext import commands, tasks
from datetime import datetime, timedelta

# Bot setup
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_CHANNEL_ID = 123456789012345678  # Replace with your channel ID
WELCOME_DM = "Welcome to the server, {username}! 🎉"

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# AI Image Generation Limits
image_count = 0
reset_time = datetime.utcnow() + timedelta(days=1)  # Reset time

@bot.command()
async def imagine(ctx, *, prompt):
    global image_count, reset_time

    if datetime.utcnow() >= reset_time:
        image_count = 0
        reset_time = datetime.utcnow() + timedelta(days=1)

    if image_count >= 20:
        await ctx.send("❌ Daily image limit reached (20 images). Try again tomorrow!")
        return

    if not OPENAI_API_KEY:
        await ctx.send("⚠️ OpenAI API key is missing.")
        return

    await ctx.send(f"🖌️ Generating an image for: **{prompt}**...")

    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response["data"][0]["url"]
        
        image_count += 1  # Increase image count
        await ctx.send(image_url)
    except Exception as e:
        await ctx.send(f"❌ Error generating image: {str(e)}")

# Auto slowmode
@bot.command()
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slowmode set to {seconds} seconds!")

# Welcome message with user avatar
@bot.event
async def on_member_join(member):
    dm_channel = await member.create_dm()
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    await dm_channel.send(f"{WELCOME_DM.format(username=member.name)}")
    await dm_channel.send(avatar_url)

# Fetch Pokémon info
@bot.command()
async def pokemon(ctx, name: str):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        await ctx.send(f"**{data['name'].capitalize()}** - Type: {', '.join([t['type']['name'] for t in data['types']])}")
    else:
        await ctx.send("❌ Pokémon not found!")

# Fetch anime quotes
@bot.command()
async def animequote(ctx):
    response = requests.get("https://animechan.xyz/api/random")
    if response.status_code == 200:
        data = response.json()
        await ctx.send(f"📜 **{data['quote']}** - {data['character']} ({data['anime']})")
    else:
        await ctx.send("❌ Couldn't fetch quote!")

# Fetch anime news
@tasks.loop(hours=1)
async def anime_news():
    channel = bot.get_channel(NEWS_CHANNEL_ID)
    if channel:
        response = requests.get("https://www.animenewsnetwork.com/news/rss.xml")
        if response.status_code == 200:
            await channel.send("📰 **Latest Anime News:** <https://www.animenewsnetwork.com>")
        else:
            await channel.send("❌ Error fetching news.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    anime_news.start()

bot.run(TOKEN)
