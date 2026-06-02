import os
import discord
from dotenv import load_dotenv
import asyncio

from functions.agents import magic_agent

import os
import sys
from dotenv import find_dotenv

load_dotenv(override=True)

TOKEN = os.getenv("DISCORD_TOKEN")

print("CWD:", os.getcwd())
print("NVIDIA:", os.getenv("NVIDIA_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"✅ Bot online: {client.user}")



def split_message(text, max_len=1900):
    chunks = []

    while len(text) > max_len:
        # Cerca un newline vicino al limite
        split_at = text.rfind("\n", 0, max_len)

        # Se non trova newline usa spazio
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)

        # Se ancora niente, taglia brutalmente
        if split_at == -1:
            split_at = max_len

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    if text:
        chunks.append(text)

    return chunks

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Risponde solo se il bot è taggato
    if client.user not in message.mentions:
        return

    question = (
        message.content
        .replace(f"<@{client.user.id}>", "")
        .replace(f"<@!{client.user.id}>", "")
        .strip()
    )

    if not question:
        await message.reply("Fammi una domanda dopo il tag 😄")
        return

    status_msg = await message.reply("🔍 Sto cercando la risposta...")

    try:
        response = await asyncio.to_thread(
            magic_agent,
            question
        )

        chunks = split_message(response)

        # Invia i chunk come messaggi separati
        for i, chunk in enumerate(chunks):
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)

    except Exception as e:
        await status_msg.edit(
            content=f"❌ Errore:\n```{e}```"
        )

client.run(TOKEN)