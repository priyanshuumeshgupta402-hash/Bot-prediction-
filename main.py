import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from config import BOT_TOKEN, CREATOR_TAG
from engine import execute_live_session, run_test_sequence
from keep_alive import keep_alive

WAIT_CHANNEL, WAIT_TRADES = range(2)
BANNER_URL = "https://i.ibb.co/tTZmsWrQ/62270897-7b06-4f65-b0cf-958f37cf6ba9.png"

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Instant Session", callback_data="menu_start_session")]
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_main")]])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"<b>🌟 ⚡ QUANTUM PREDICTION AUTOMATION V59 ⚡ 🌟</b>\n"
        f"<b>──────────────────────────────</b>\n"
        f"<b>🤖 Developer:</b> {CREATOR_TAG}\n"
        f"<b>💡 Status:</b> Instant Mode Ready.\n\n"
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
    success, err_msg = await run_test_sequence(channel)
    if success:
        await update.message.reply_text(f"<b>✅ Test successful! Check your channel <code>{channel}</code> for sticker & chart.</b>", parse_mode="HTML")
    else:
        await update.message.reply_text(f"<b>❌ Test failed!\nTelegram Error: <code>{err_msg}</code></b>", parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        text = f"<b>🌟 ⚡ QUANTUM PREDICTION AUTOMATION V59 ⚡ 🌟</b>\n<b>👇 Choose an option from the menu below:</b>"
        try:
            await query.message.reply_photo(photo=BANNER_URL, caption=text, reply_markup=main_menu(), parse_mode="HTML")
            await query.message.delete()
        except Exception:
            await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML")
        return ConversationHandler.END

    elif data == "menu_start_session":
        await query.edit_message_caption(
            caption="<b>🚀 START INSTANT SESSION</b>\n\n<b>Step 1/2: Send target channel username or link (e.g., @Cash_with_raja):</b>",
            reply_markup=back_menu(), parse_mode="HTML"
        )
        return WAIT_CHANNEL

    return ConversationHandler.END

async def receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["channel"] = update.message.text.strip()
    await update.message.reply_text("<b>📊 Step 2/2: How many trades do you want to send? (e.g., 10, 15):</b>", parse_mode="HTML")
    return WAIT_TRADES

async def receive_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        total_trades = int(update.message.text.strip())
    except ValueError:
        total_trades = 10
        
    channel = context.user_data.get("channel")
    
    await update.message.reply_text(
        f"<b>🚀 Session Started Successfully!</b>\n\n"
        f"📢 <b>Channel:</b> <code>{channel}</code>\n"
        f"🎯 <b>Total Trades:</b> <code>{total_trades}</code>\n\n"
        f"<b>📌 Bot has started sending signals to the channel right now!</b>", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]])
    )
    
    # Session turant background task mein chalu ho jayega
    asyncio.create_task(execute_live_session(channel, total_trades))
    return ConversationHandler.END

def main():
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            WAIT_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel), CallbackQueryHandler(button_handler)],
            WAIT_TRADES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trades), CallbackQueryHandler(button_handler)]
        },
        fallbacks=[CommandHandler("start", start_cmd), CallbackQueryHandler(button_handler)],
        per_message=False
    )
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(conv)
    print("🔥 Instant Prediction Bot is live!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
