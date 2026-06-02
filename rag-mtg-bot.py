import os
import asyncio
import discord

from dotenv import load_dotenv

from functions.agents import magic_agent
from functions.chroma import setup_chroma_index

load_dotenv(override=True)
indexing_lock = asyncio.Lock()

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_USER_ID = 140165676064047104

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================
# UTILITIES
# =========================

def split_message(text, max_len=1900):
    chunks = []

    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)

        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)

        if split_at == -1:
            split_at = max_len

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    if text:
        chunks.append(text)

    return chunks


def is_admin(message):
    return message.author.id == ADMIN_USER_ID


async def run_indexing():

    async with indexing_lock:

        await asyncio.to_thread(
            setup_chroma_index
        )

        return "✅ Indicizzazione completata."


# =========================
# COMMAND HANDLERS
# =========================

async def handle_ask(message, args):

    if not args:
        await message.reply(
            "Uso corretto:\n`!ask <domanda>`"
        )
        return

    status_msg = await message.reply(
        "🔍 Sto cercando la risposta..."
    )

    try:

        response = await asyncio.to_thread(
            magic_agent,
            args
        )

        await status_msg.delete()

        chunks = split_message(response)

        for i, chunk in enumerate(chunks):

            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)

    except Exception as e:

        await status_msg.edit(
            content=f"❌ Errore:\n```{e}```"
        )


async def handle_index(message, args):
    if not is_admin(message):
        await message.reply("⛔ Non sei autorizzato.")
        return

    # 1. Controlla se il lock è già acquisito da un'altra chiamata in corso
    if indexing_lock.locked():
        await message.reply(
            "⏳ Sto già indicizzando il regolamento di MTG."
        )
        return
        
    status_msg = await message.reply(
        "📚 Avvio indicizzazione..."
    )
    
    try:
        # 2. Chiama la funzione helper che gestisce in sicurezza il Lock e il thread
        risultato = await run_indexing()
        
        await status_msg.edit(content=risultato)
        
    except Exception as e:
        await status_msg.edit(
            content=f"❌ Errore:\n```{e}```"
        )


async def handle_help(message, args):

    await message.reply(
        """
**Comandi disponibili**

`!ask <domanda>`
Interroga il knowledge base.

`!index`
Ricostruisce l'indice (solo Poppo).

`!help`
Mostra questo messaggio.
        """
    )


# =========================
# DISPATCHER
# =========================

COMMANDS = {
    "ask": handle_ask,
    "index": handle_index,
    "help": handle_help,
}


# =========================
# EVENTS
# =========================

@client.event
async def on_ready():
    print(f"✅ Bot online: {client.user}")


@client.event
async def on_message(message):

    if message.author.bot:
        return

    if not message.content.startswith("!"):
        return

    parts = message.content[1:].split(
        maxsplit=1
    )

    command = parts[0].lower()

    args = (
        parts[1].strip()
        if len(parts) > 1
        else ""
    )

    handler = COMMANDS.get(command)

    if handler:
        await handler(message, args)
    else:
        await message.reply(
            f"❓ Comando sconosciuto: `{command}`\nUsa `!help`."
        )


client.run(TOKEN)