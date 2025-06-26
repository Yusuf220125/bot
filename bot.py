from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

ADMIN_ID = 1350513135  # <-- o'zingizning Telegram ID'ingizni yozing
BOT_TOKEN = "8046803096:AAH625U_9kRIErhsgZ8Dl7-qOoaXFAzb2CQ"  # <-- bu yerga bot tokenni yozing

# Video bazasi: "kod": file_id
VIDEO_DICT = {}

# Kanallar ro'yxati (obuna bo'lish majburiy)
REQUIRED_CHANNELS = ["@kanal_nomi1", "@kanal_nomi2"]

# Obuna tekshirish funksiyasi
async def check_subscription(user_id, bot):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id, context.bot)

    if is_subscribed:
        await update.message.reply_text("Xush kelibsiz! 3 xonali kodni kiriting yoki admin uchun /upload buyrug'ini yozing.")
    else:
        buttons = [
            [InlineKeyboardButton("📢 Kanal 1", url="https://t.me/kanal_nomi1")],
            [InlineKeyboardButton("📢 Kanal 2", url="https://t.me/kanal_nomi2")],
            [InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_again")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:", reply_markup=reply_markup)

# Obuna qayta tekshirish
async def check_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    is_subscribed = await check_subscription(user_id, context.bot)

    if is_subscribed:
        await query.message.reply_text("✅ Obuna tekshiruvdan muvaffaqiyatli o‘tdingiz! 3 xonali kodni yuboring.")
    else:
        await query.message.reply_text("❗ Hali ham obuna bo‘lmagansiz. Iltimos, barcha kanallarga obuna bo‘ling.")

# /upload buyrug'i - admin uchun
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Sizga ruxsat yo‘q.")
        return
    await update.message.reply_text("🎥 Videoni yuboring.")
    context.user_data['uploading'] = True

# Admindan video qabul qilish
async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get('uploading'):
        file_id = update.message.video.file_id
        context.user_data['file_id'] = file_id
        context.user_data['uploading'] = False
        await update.message.reply_text("✅ Video qabul qilindi. Endi unga nom yozing:")
        context.user_data['awaiting_name'] = True

# Admin matn yuborganida - nom, kod, yoki foydalanuvchi kiritgan kod
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id == ADMIN_ID:
        if context.user_data.get('awaiting_name'):
            context.user_data['name'] = text
            context.user_data['awaiting_name'] = False
            await update.message.reply_text("🔢 Endi videoga mos 3 xonali raqam kiriting:")
            context.user_data['awaiting_code'] = True
            return

        if context.user_data.get('awaiting_code'):
            if text.isdigit() and len(text) <= 3:
                VIDEO_DICT[text] = context.user_data['file_id']
                await update.message.reply_text(f"✅ Video saqlandi! Kod: {text}, Nomi: {context.user_data['name']}")
                context.user_data.clear()
            else:
                await update.message.reply_text("❗ Iltimos, 3 xonali son kiriting.")
            return

    # Oddiy foydalanuvchi kod yuborgan bo‘lsa
    if text.isdigit() and len(text) <= 3:
        file_id = VIDEO_DICT.get(text)
        if file_id:
            await update.message.reply_video(video=file_id)
        else:
            await update.message.reply_text("❌ Bunday kodga mos video topilmadi.")
    else:
        await update.message.reply_text("❗ Iltimos, faqat 3 xonali raqam kiriting.")

# Bot ishga tushirish
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_again, pattern="check_again"))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot ishga tushdi!")
    app.run_polling()
