"""
NekoMusic — String Session Generator
Run this ONCE locally to generate STRING_SESSION for your assistant account.

    python generate_session.py

Then copy the printed session string into your .env or Heroku config vars.
"""

import asyncio

API_ID   = int(input("Enter API_ID   : ").strip())
API_HASH = input("Enter API_HASH : ").strip()


async def generate():
    from pyrogram import Client
    async with Client("assistant_temp", api_id=API_ID, api_hash=API_HASH) as app:
        session = await app.export_session_string()
        print("\n" + "=" * 70)
        print("YOUR STRING SESSION (copy this entire line):")
        print("=" * 70)
        print(session)
        print("=" * 70)
        print("\n⚠️  Keep this secret — it grants full account access!\n")


asyncio.run(generate())
