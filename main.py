import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# Load environment variables
load_dotenv()

# Conversation states
IMAGE_WAIT, IMG_DETAILS = 1, 2

# Configuration
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS').split(',')]
DEFAULT_QUALITIES = os.getenv('DEFAULT_QUALITIES').split(',')

# Command handlers
async def set_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /setquality quality1,quality2,...")
        return
    qualities = [q.strip() for q in args[1].split(',')]
    context.chat_data["qualities"] = qualities
    await update.message.reply_text(f"Qualities set to: {qualities}")

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /setcaption <your template>")
        return
    context.chat_data["caption_template"] = args[1]
    await update.message.reply_text("Caption template updated!")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized!")
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /ban @username")
        return
    username_to_ban = args[1].strip().lstrip('@')
    context.bot_data.setdefault('banned_users', set()).add(username_to_ban)
    await update.message.reply_text(f"User @{username_to_ban} banned.")

async def set_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("Usage: /setbatch <channel_username_or_id>")
        return
    context.chat_data["batch_channel"] = args[1].strip()
    await update.message.reply_text(f"Batch channel set to: {args[1].strip()}")

async def imgcap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send the image to caption.")
    return IMAGE_WAIT

async def process_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return IMAGE_WAIT
    context.chat_data["img_file_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(
        "Send details in 4 lines:\n"
        "1. Anime Name\n2. Status\n3. Season\n4. Episodes"
    )
    return IMG_DETAILS

async def process_img_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.split('\n')
    if len(details) < 4:
        await update.message.reply_text("Need 4 details. Try again.")
        return IMG_DETAILS
    caption_template = context.chat_data.get(
        "caption_template",
        "<b>🦋 Anime Name: {name}</b>\n"
        "<b>🎴 Status: {status}</b>\n"
        "<b>🏮 Season: {season}</b>\n"
        "<b>🔮 Episodes: {episodes}</b>\n"
        "<b>🔈 Audio: Hindi</b>\n"
        "<b>📥 Quality: {qualities}</b>\n"
        "<b><blockquote>📌 Tags: #AnimeLovers #HindiDubbedAnime</blockquote></b>"
    )
    qualities = context.chat_data.get("qualities", DEFAULT_QUALITIES)
    caption = caption_template.format(
        name=details[0].strip(),
        status=details[1].strip(),
        season=details[2].strip(),
        episodes=details[3].strip(),
        qualities=", ".join(qualities)
    await update.message.reply_photo(
        photo=context.chat_data["img_file_id"],
        caption=caption,
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('imgcap', imgcap_start)],
        states={
            IMAGE_WAIT: [
                MessageHandler(filters.PHOTO, process_img),
                CommandHandler('cancel', cancel)
            ],
            IMG_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_img_details),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setquality", set_quality))
    app.add_handler(CommandHandler("setcaption", set_caption))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("setbatch", set_batch))
    app.add_handler(conv_handler)
    
    app.run_polling()

if __name__ == "__main__":
    main()
