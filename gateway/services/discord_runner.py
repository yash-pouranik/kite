import asyncio
import logging
import discord
from discord.ext import commands
from config import settings
from agents.agent_engine import KiteAgentEngine

logger = logging.getLogger("cyberwar.discord_runner")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Instantiate the single powerful Agent Engine
agent_engine = KiteAgentEngine()

@bot.event
async def on_ready():
    logger.info(f"🪁 Kite Bot is online in Discord as @{bot.user.name} (ID: {bot.user.id})")
    print(f"\n[Kite Bot Connected] Logged in as {bot.user.name}\n")

@bot.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author.bot:
        return

    content = message.content.strip()
    logger.info(f"Received message from {message.author.name} in #{message.channel.name}: {content}")

    # 1. Fetch channel message history for true Switch Room Context
    room_history = []
    try:
        async for prev_msg in message.channel.history(limit=6, oldest_first=False):
            author_name = "Kite-Agent" if prev_msg.author.bot else prev_msg.author.name
            room_history.append(f"{author_name}: {prev_msg.content.strip()}")
        room_history.reverse()
    except Exception as e:
        logger.warning(f"Could not fetch room history: {e}")
        room_history = [f"{message.author.name}: {content}"]

    # 2. Let the Agent Engine process the turn with OpenAI Function Calling
    async with message.channel.typing():
        response_text = await agent_engine.process_chat_turn(
            user_message=content,
            room_history=room_history
        )

        # Discord message limit is 2000 chars, split if necessary
        if len(response_text) > 1950:
            for chunk in [response_text[i:i+1900] for i in range(0, len(response_text), 1900)]:
                await message.channel.send(chunk)
        else:
            await message.channel.send(response_text)

async def start_discord_bot():
    token = settings.DISCORD_BOT_TOKEN
    if not token or token == "your_discord_bot_token_here":
        logger.warning("DISCORD_BOT_TOKEN not provided in .env. Discord listener standing by.")
        return
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting Discord Bot: {e}")
