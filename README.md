# Telegram Video Delivery Bot

**Created:** 2025-06-26

## Features
1. Forced subscription to specified channels.
2. Asks user for a *code* and sends the mapped video.
3. `/upload` and `/delete` commands for owners/admins.

## Quick start
```bash
pip install python-telegram-bot[tgcrypto]==21.* aiosqlite
export BOT_TOKEN=<YOUR_BOT_TOKEN>
python telegram_video_bot.py
```

Edit `telegram_video_bot.py`:
- Replace `MANDATORY_CHANNELS` with your channel IDs.
- Replace `ADMIN_IDS` with your Telegram user IDs.
