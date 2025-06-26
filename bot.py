"""
Telegram Video Delivery Bot
--------------------------
Features
1. Forced subscription to mandatory channels before access.
2. After verification, asks the user for a code; replies with the corresponding video.
3. Owners/admins can upload and delete videos via /upload and /delete commands.

Setup
-----
1. Install dependencies:
   pip install python-telegram-bot[tgcrypto]==21.* aiosqlite
2. Fill in the configuration section with your bot token,
   mandatory channel IDs, and admin user IDs.
3. Run: python bot.py

Author: ChatGPT (OpenAI o3)
Date: 26 June 2025
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import List

import aiosqlite
from telegram import ChatMember, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

########################
# ------- CONFIG ------
########################
TOKEN = os.getenv("BOT_TOKEN", "8046803096:AAH625U_9kRIErhsgZ8Dl7-qOoaXFAzb2CQ")
MANDATORY_CHANNELS: List[int] = [
    -1001234567890,  # replace with your channel IDs (must be negative ints)
    # -1009876543210,
]
ADMIN_IDS: List[int] = [1350513135]  # numeric Telegram user IDs who can manage videos
DB_PATH = "videos.db"

########################
# ---- LOGGING SETUP --
########################
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

########################
# ---- DATABASE LAYER -
########################

@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS videos (
                    code TEXT PRIMARY KEY,
                    title TEXT,
                    file_id TEXT
                )"""
        )
        await db.commit()
        yield db

async def add_video(code: str, title: str, file_id: str):
    async with get_db() as db:
        await db.execute(
            "REPLACE INTO videos (code, title, file_id) VALUES (?,?,?)",
            (code.upper(), title, file_id),
        )
        await db.commit()

async def delete_video(code: str) -> bool:
    async with get_db() as db:
        cur = await db.execute("DELETE FROM videos WHERE code=?", (code.upper(),))
        await db.commit()
        return cur.rowcount > 0

async def fetch_video(code: str):
    async with get_db() as db:
        cur = await db.execute(
            "SELECT file_id, title FROM videos WHERE code=?", (code.upper(),)
        )
        return await cur.fetchone()  # (file_id, title) or None

########################
# ---- HELPERS --------
########################

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_membership(user_id: int, context: CallbackContext) -> bool:
    """Return True if user is a member of all mandatory channels."""
    for channel_id in MANDATORY_CHANNELS:
        try:
            member: ChatMember = await context.bot.get_chat_member(channel_id, user_id)
            if member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.ADMINISTRATOR,
            ):
                return False
        except BadRequest:
            return False  # maybe bot isn't admin in the channel
    return True

########################
# ---- HANDLERS -------
########################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    if await check_membership(user.id, context):
        await update.message.reply_text(
            "✅ Kanal(a)larga a'zolik tasdiqlandi!\n" "Iltimos, videoni olish uchun kodni kiriting:",
        )
        # Mark user as verified in conversation data
        context.user_data["verified"] = True
    else:
        buttons = [
            [InlineKeyboardButton("➕ Kanalga qo'shiling", url=f"https://t.me/c/{KINOSPEEDS}")]
            for channel in MANDATORY_CHANNELS
        ]
        await update.message.reply_text(
            "Salom! Videoni olishdan oldin quyidagi kanal(lar)ga a'zo bo'ling:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("verified"):
        return  # Only accept codes from verified users
    code = update.message.text.strip()
    row = await fetch_video(code)
    if row:
        file_id, title = row
        await update.message.reply_video(
            video=file_id,
            caption=f"📹 <b>{title}</b>\nKod: <code>{code.upper()}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            "🚫 Bunday kod topilmadi. To'g'ri kiriting yoki /start buyrug'ini qayta bajaring."
        )

########################
# ---- ADMIN HANDLERS -
########################

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not (user and is_admin(user.id)):
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.video:
        await update.message.reply_text(
            "⬆️ Videoni yuklash uchun avval videoga javob sifatida /upload <code> <nom> deb yozing."
        )
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Foydalanish: /upload <kod> <nom>")
        return

    code = args[0]
    title = " ".join(args[1:])
    file_id = update.message.reply_to_message.video.file_id

    await add_video(code, title, file_id)
    await update.message.reply_text(f"✅ Video saqlandi! Kod: {code.upper()} -> {title}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not (user and is_admin(user.id)):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Foydalanish: /delete <kod>")
        return
    code = context.args[0]
    success = await delete_video(code)
    if success:
        await update.message.reply_text(f"🗑️ {code.upper()} kodi bilan video o'chirildi.")
    else:
        await update.message.reply_text("🚫 Bunday kod topilmadi.")

########################
# ---- MAIN -----------
########################

def main():
    if TOKEN.startswith("PASTE_"):
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisiga tokenni joylang!")

    application: Application = (
        ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    )

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("delete", delete))

    # Text messages handled as codes (after /start verification)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code)
    )

    # Start long-polling (blocks)
    logger.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    import asyncio, platform

    # Windows uchun: Proactor o‘rniga Selector loop siyosati — xatoni bartaraf etadi
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    main()
