import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from config import BOT_TOKEN, CREATOR_TAG
from database import init_db, add_channel_db, get_user_channels, get_all_configured_channels
from engine import start_session_workflow, run_test_sequence
from keep_alive import keep_alive

WAIT_CHANNEL, WAIT_TIME = range(2)
BANNER_URL = "https://i.ibb.co/tTZmsWrQ/62270897-7b06-4f65-b0cf-958f37cf6ba9.png"

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Configured Channels", callback_data="menu_settings")],
        [InlineKeyboardButton("➕ Add Channel & Session Time", callback_data="menu_add_channel")]
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_main")]])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"<b>🌟 ⚡ QUANTUM PREDICTION AUTOMATION V59 ⚡ 🌟</b>\n"
        f"<b>──────────────────────────────</b>\n"
        f"<b>🤖 Developer:</b> {CREATOR_TAG}\n"
        f"<b>💡 Status:</b> Ready for Auto Channel Signals.\n\n"
        f"<b>👇 Choose an option from the menu below:</b>"
    )
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.reply_photo(photo=BANNER_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")
            await update.callback_query.message.delete()
        except Exception:
            await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML")
    else:
        await update.message.reply_photo(photo=BANNER_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")
    return ConversationHandler.END

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("<b>⚠️ Please provide channel username!\nExample: <code>/test @Cash_with_raja</code></b>", parse_mode="HTML")
        return
    channel = context.args[0]
    await update.message.reply_text(f"<b>🚀 Testing connection on <code>{channel}</code>...</b>", parse_mode="HTML")
    success = await run_test_sequence(channel)
    if success:
        await update.message.reply_text(f"<b>✅ Test successful! Check your channel <code>{channel}</code> for sticker & chart.</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"<b>❌ Test failed! Make sure the bot is an ADMIN in <code>{channel}</code> and username is correct. Check Render Logs.</b>", parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back_main":
        text = f"<b>🌟 ⚡ QUANTUM PREDICTION AUTOMATION V59 ⚡ 🌟</b>\n<b>👇 Choose an option from the menu below:</b>"
        try:
            await query.message.reply_photo(photo=BANNER_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")
            await query.message.delete()
        except Exception:
            await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML")
        return ConversationHandler.END

    elif data == "menu_add_channel":
        await query.edit_message_caption(
            caption="<b>➕ ADD CHANNEL FOR PREDICTIONS</b>\n\n<b>Send target channel username (e.g., @Cash_with_raja):</b>",
            reply_markup=back_menu(), parse_mode="HTML"
        )
        return WAIT_CHANNEL

    elif data == "menu_settings":
        channels = await get_user_channels(user_id)
        ch_list = "\n".join([f"• <code>{c[0]}</code> (Time: {c[1]}) - <b>{c[2]}</b>" for c in channels]) if channels else "No channels configured yet."
        text = f"<b>⚙️ YOUR CONFIGURED CHANNELS:</b>\n\n{ch_list}"
        await query.edit_message_caption(caption=text, reply_markup=back_menu(), parse_mode="HTML")

    return ConversationHandler.END

async def receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["channel"] = update.message.text.strip()
    await update.message.reply_text("<b>⏰ Send session start time in 24-hour format (e.g., 15:00 for 3:00 PM IST):</b>", parse_mode="HTML")
    return WAIT_TIME

async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session_time = update.message.text.strip()
    channel = context.user_data.get("channel")
    
    await add_channel_db(user_id, channel, session_time)
    asyncio.create_task(start_session_workflow(channel, session_time))
    
    await update.message.reply_text(
        f"<b>✅ Channel <code>{channel}</code> configured successfully!\n⏰ Session Start Time: {session_time} (IST)\n\n📌 Note: Make sure the bot is added as an ADMIN in <code>{channel}</code>!</b>", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]])
    )
    return ConversationHandler.END

async def post_init_setup(application: Application):
    await init_db()
    channels = await get_all_configured_channels()
    for channel, session_time in channels:
        asyncio.create_task(start_session_workflow(channel, session_time))
    print(f"🔥 Resumed background workflows for {len(channels)} channels!")

def main():
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init_setup).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            WAIT_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel), CallbackQueryHandler(button_handler)],
            WAIT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time), CallbackQueryHandler(button_handler)]
        },
        fallbacks=[CommandHandler("start", start_cmd), CallbackQueryHandler(button_handler)],
        per_message=False
    )
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(conv)
    print("🔥 Prediction Bot V59 is live!")
    app.run_polling()

if __name__ == "__main__":
    main()
        
