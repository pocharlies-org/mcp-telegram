#!/usr/bin/env python3
"""One-time authentication script. Run this interactively to create a Telegram session."""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.path.join(os.path.dirname(__file__), os.environ.get("TELEGRAM_SESSION_NAME", "session"))


async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"Authenticated as: {me.first_name} {me.last_name or ''} (@{me.username})")
    print(f"Phone: {me.phone}")
    print(f"Session saved to: {SESSION}.session")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
