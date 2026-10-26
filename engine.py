import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from telegram import Bot
from config import (
    BOT_TOKEN, SECTION_START_STICKER, WIN_STICKER, 
    JACKPOT_STICKER, SECTION_CLOSE_STICKER, LEVEL_CHART_IMG
)

bot = Bot(token=BOT_TOKEN)
API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

def get_ist_time():
    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    return ist_now.strftime("%H:%M")

def normalize_time(t_str):
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 2:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    except Exception:
        pass
    return t_str.strip()

async def run_test_sequence(channel: str):
    try:
        print(f"🧪 Running test sequence for {channel}")
        if SECTION_START_STICKER:
            await bot.send_sticker(chat_id=channel, sticker=SECTION_START_STICKER)
        await asyncio.sleep(2)
        if LEVEL_CHART_IMG:
            await bot.send_photo(chat_id=channel, photo=LEVEL_CHART_IMG, caption="<b>📊 TEST CHART - BOT IS LIVE</b>", parse_mode="HTML")
        return True
    except Exception as e:
        print(f"Test error in channel {channel}: {e}")
        return False

def to_bold_unicode(str_val):
    bold_map = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚',
        'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡',
        'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨',
        'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴',
        'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻',
        'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂',
        'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',
        '(': '(', ')': ')', ',': ',', ' ': ' ', '-': '-'
    }
    return ''.join([bold_map.get(c, c) for c in str(str_val)])

async def fetch_latest_history():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API + "?t=" + str(int(datetime.now().timestamp()*1000))) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {}).get("list", [])
        except Exception:
            pass
        return []

def generate_v59_prediction(list_data, nextP):
    if not list_data:
        return {"period": str(nextP), "betType": "BIG", "n1": 5, "n2": 8}
    
    history = [int(x["number"]) for x in list_data[:20] if str(x["number"]).isdigit()]
    if not history:
        return {"period": str(nextP), "betType": "SMALL", "n1": 3, "n2": 6}
    
    last_num = history[0]
    bet_type = "BIG" if last_num < 5 else "SMALL"
    n1 = (last_num + 2) % 10
    n2 = (last_num + 5) % 10
    return {"period": str(nextP), "betType": bet_type, "n1": n1, "n2": n2}

async def start_session_workflow(channel: str, session_time: str):
    target_time = normalize_time(session_time)
    print(f"🚀 Session Workflow initialized for channel {channel} at target time {target_time} IST")
    
    while True:
        current_time = get_ist_time()
        if current_time == target_time:
            try:
                print(f"🔥 Session started for {channel}!")
                if SECTION_START_STICKER:
                    await bot.send_sticker(chat_id=channel, sticker=SECTION_START_STICKER)
                
                await asyncio.sleep(3)
                if LEVEL_CHART_IMG:
                    await bot.send_photo(chat_id=channel, photo=LEVEL_CHART_IMG, caption="<b>📊 MAINTAIN 3-LEVEL FUNDS</b>", parse_mode="HTML")

                await asyncio.sleep(5)

                for trade_num in range(1, 11):
                    list_data = await fetch_latest_history()
                    if list_data:
                        latest_issue = str(list_data[0]["issueNumber"])
                        nextP = str(int(latest_issue) + 1)
                        
                        pred = generate_v59_prediction(list_data, nextP)
                        period_short = pred["period"][-3:]
                        
                        bold_period = to_bold_unicode(f"PERIOD NO - {period_short}")
                        bold_bet_type = to_bold_unicode(pred["betType"])
                        bold_nums = to_bold_unicode(f"{pred['n1']} , {pred['n2']}")
                        
                        msg_text = f"‼️ {bold_period}\n\n📈 {bold_bet_type} ➔ {bold_nums}"
                        sent_msg = await bot.send_message(chat_id=channel, text=msg_text)
                        
                        await asyncio.sleep(55)
                        
                        new_list = await fetch_latest_history()
                        hit = next((x for x in new_list if str(x["issueNumber"]) == pred["period"]), None)
                        if hit:
                            res_num = int(hit["number"])
                            res_sz = "BIG" if res_num >= 5 else "SMALL"
                            is_win = (res_sz == pred["betType"])
                            is_jackpot = (res_num == pred["n1"] or res_num == pred["n2"])
                            
                            if is_jackpot:
                                status_str = "💎 JACKPOT WIN"
                                if JACKPOT_STICKER:
                                    await bot.send_sticker(chat_id=channel, sticker=JACKPOT_STICKER)
                            elif is_win:
                                status_str = "✅ WIN"
                                if WIN_STICKER:
                                    await bot.send_sticker(chat_id=channel, sticker=WIN_STICKER)
                            else:
                                status_str = "❌ LOSS"
                            
                            updated_text = f"{msg_text}\n\nRESULT: {res_num} ({res_sz}) - {status_str}"
                            await bot.edit_message_text(chat_id=channel, message_id=sent_msg.message_id, text=updated_text)
                    
                    await asyncio.sleep(10)

                if SECTION_CLOSE_STICKER:
                    await asyncio.sleep(2)
                    await bot.send_sticker(chat_id=channel, sticker=SECTION_CLOSE_STICKER)

                await asyncio.sleep(120)
            except Exception as e:
                print(f"Workflow error in channel {channel}: {e}")
        
        await asyncio.sleep(30)
                
