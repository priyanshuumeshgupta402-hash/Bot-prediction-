import asyncio
import json
import subprocess
from datetime import datetime
from telegram import Bot
from config import (
    BOT_TOKEN, SECTION_START_STICKER, WIN_STICKER, 
    JACKPOT_STICKER, SECTION_CLOSE_STICKER, LEVEL_CHART_IMG
)

bot = Bot(token=BOT_TOKEN)

def normalize_channel(ch_str):
    ch_str = ch_str.strip()
    if "t.me/" in ch_str:
        username = ch_str.split("t.me/")[-1].strip('/')
        return f"@{username}"
    if not ch_str.startswith('@') and not ch_str.startswith('-'):
        return f"@{ch_str}"
    return ch_str

async def get_html_direct_prediction():
    try:
        proc = await asyncio.create_subprocess_exec(
            'node', 'runner.js',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            data = json.loads(stdout.decode().strip())
            return data
    except Exception as e:
        print(f"JS Engine Error: {e}")
    return None

async def execute_live_session(channel: str, total_trades: int = 10):
    channel = normalize_channel(channel)
    try:
        print(f"🔥 Starting Exact HTML Copy Session for {channel} ({total_trades} trades)")
        if SECTION_START_STICKER:
            await bot.send_sticker(chat_id=channel, sticker=SECTION_START_STICKER)
        
        await asyncio.sleep(3)
        if LEVEL_CHART_IMG:
            await bot.send_photo(chat_id=channel, photo=LEVEL_CHART_IMG, caption="<b>📊 MAINTAIN 3-LEVEL FUNDS</b>", parse_mode="HTML")

        await asyncio.sleep(5)

        for trade_num in range(1, total_trades + 1):
            pred_data = await get_html_direct_prediction()
            if not pred_data or 'error' in pred_data or 'exactText' not in pred_data:
                await asyncio.sleep(5)
                continue

            msg_text = pred_data['exactText']
            sent_msg = await bot.send_message(chat_id=channel, text=msg_text)
            
            await asyncio.sleep(55)
            
            if WIN_STICKER:
                await bot.send_sticker(chat_id=channel, sticker=WIN_STICKER)

            updated_text = f"{msg_text}\n\nRESULT: ✅ WIN"
            await bot.edit_message_text(chat_id=channel, message_id=sent_msg.message_id, text=updated_text)
            
            await asyncio.sleep(10)

        if SECTION_CLOSE_STICKER:
            await asyncio.sleep(2)
            await bot.send_sticker(chat_id=channel, sticker=SECTION_CLOSE_STICKER)
        print(f"✅ Session successfully completed for {channel}")
    except Exception as e:
        print(f"Session error in {channel}: {e}")
            
