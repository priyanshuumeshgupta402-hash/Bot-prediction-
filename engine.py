import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot
from config import (
    BOT_TOKEN, SECTION_START_STICKER, WIN_STICKER, 
    JACKPOT_STICKER, SECTION_CLOSE_STICKER, LEVEL_CHART_IMG
)

bot = Bot(token=BOT_TOKEN)
API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

def normalize_channel(ch_str):
    ch_str = ch_str.strip()
    if "t.me/" in ch_str:
        username = ch_str.split("t.me/")[-1].strip('/')
        return f"@{username}"
    if not ch_str.startswith('@') and not ch_str.startswith('-'):
        return f"@{ch_str}"
    return ch_str

async def run_test_sequence(channel: str):
    channel = normalize_channel(channel)
    try:
        if SECTION_START_STICKER:
            await bot.send_sticker(chat_id=channel, sticker=SECTION_START_STICKER)
        await asyncio.sleep(2)
        if LEVEL_CHART_IMG:
            await bot.send_photo(chat_id=channel, photo=LEVEL_CHART_IMG, caption="<b>📊 TEST CHART - BOT IS LIVE</b>", parse_mode="HTML")
        return True, "Success"
    except Exception as e:
        return False, str(e)

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

def period_seed(period):
    h = 2166136261
    s = str(period)
    for i in range(len(s)):
        h ^= ord(s[i])
        h = (h * 16777619) & 0xFFFFFFFF
    return h

def mulberry32(seed):
    def rng():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed
        t = (t ^ (t >> 15)) * (t | 1)
        t &= 0xFFFFFFFF
        t ^= t + ((t ^ (t >> 7)) * 61)
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) >> 0) / 4294967296
    return rng

def pick_numbers_history(history, pool, period):
    if not pool:
        pool = [5, 6, 7, 8, 9]
    if not history:
        return {"n1": pool[0], "n2": pool[-1]}
    
    last_num = history[0]
    scored = []
    for num in pool:
        score = 0
        freq = history[:40].count(num)
        score += freq * 2
        
        last_seen = history.index(num) if num in history else 60
        if 5 <= last_seen <= 15:
            score += 40
        elif 16 <= last_seen <= 25:
            score += 25
        elif last_seen > 25:
            score += 30
        
        d = abs(last_num - num)
        if d == 1: score += 18
        if d == 2: score += 10
        
        scored.append({"num": num, "score": score})
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    n1 = scored[0]["num"]
    n2 = scored[1]["num"] if len(scored) > 1 else scored[0]["num"]
    if n1 == n2:
        alt = next((s["num"] for s in scored if s["num"] != n1), (pool[0] if pool[0] != n1 else pool[1]))
        n2 = alt
    return {"n1": n1, "n2": n2}

def generate_deep_v59_prediction(list_data, nextP):
    """DeepSeek HTML file ka exact V59 Pure Size Prediction Logic"""
    if not list_data:
        return {"period": str(nextP), "betType": "BIG", "n1": 5, "n2": 8}
    
    history = [int(x["number"]) for x in list_data[:60] if str(x["number"]).isdigit()]
    if not history:
        return {"period": str(nextP), "betType": "SMALL", "n1": 3, "n2": 6}
    
    types = ["BIG" if n >= 5 else "SMALL" for n in history]
    
    size_score = 0
    sz_streak = 1
    for i in range(1, len(types)):
        if types[i] == types[0]: sz_streak += 1
        else: break
        
    r5 = types[:5].count("BIG") / 5 if len(types) >= 5 else 0.5
    r10 = types[:10].count("BIG") / 10 if len(types) >= 10 else 0.5
    
    if r5 >= 0.8: size_score += 50
    elif r5 <= 0.2: size_score -= 50
    if r10 >= 0.7: size_score += 30
    elif r10 <= 0.3: size_score -= 30
    if sz_streak >= 2:
        size_score += (30 if types[0] == "BIG" else -30)
        
    bet_type = "BIG" if size_score >= 0 else "SMALL"
    
    main_pool = [5, 6, 7, 8, 9] if bet_type == "BIG" else [0, 1, 2, 3, 4]
    opp_pool = [0, 1, 2, 3, 4] if bet_type == "BIG" else [5, 6, 7, 8, 9]
    
    main_nums = pick_numbers_history(history, main_pool, nextP)
    opp_nums = pick_numbers_history(history, opp_pool, str(nextP) + "opp")
    
    n1 = main_nums["n1"]
    n2 = opp_nums["n1"]
    if n1 == n2:
        alt = next((p for p in opp_pool if p != n1), main_pool[0])
        n2 = alt
        
    return {"period": str(nextP), "betType": bet_type, "n1": n1, "n2": n2}

async def execute_live_session(channel: str, total_trades: int = 10):
    channel = normalize_channel(channel)
    try:
        print(f"🔥 Starting Quantum Deep V59 session for {channel} with {total_trades} trades")
        if SECTION_START_STICKER:
            await bot.send_sticker(chat_id=channel, sticker=SECTION_START_STICKER)
        
        await asyncio.sleep(3)
        if LEVEL_CHART_IMG:
            await bot.send_photo(chat_id=channel, photo=LEVEL_CHART_IMG, caption="<b>📊 MAINTAIN 3-LEVEL FUNDS</b>", parse_mode="HTML")

        await asyncio.sleep(5)

        for trade_num in range(1, total_trades + 1):
            list_data = await fetch_latest_history()
            
            if list_data and len(list_data) > 0 and str(list_data[0].get("issueNumber", "")).isdigit():
                latest_issue = str(list_data[0]["issueNumber"])
                nextP = str(int(latest_issue) + 1)
            else:
                nextP = str(int(datetime.now().timestamp() * 1000) % 1000000000)
            
            pred = generate_deep_v59_prediction(list_data, nextP)
            
            # HTML file ki tarah exact last 3 digits period number (jaise 723)
            period_full = str(pred["period"])
            period_short = period_full[-3:] if len(period_full) >= 3 else period_full.zfill(3)
            
            bold_period = to_bold_unicode(f"PERIOD NO - {period_short}")
            bold_bet_type = to_bold_unicode(pred["betType"])
            bold_nums = to_bold_unicode(f"{pred['n1']} , {pred['n2']}")
            
            msg_text = f"‼️ {bold_period}\n\n📈 {bold_bet_type} ➔ {bold_nums}"
            sent_msg = await bot.send_message(chat_id=channel, text=msg_text)
            
            await asyncio.sleep(55)
            
            new_list = await fetch_latest_history()
            hit = None
            if new_list:
                hit = next((x for x in new_list if str(x.get("issueNumber")) == pred["period"]), None)
            
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
            else:
                updated_text = f"{msg_text}\n\nRESULT: N/A"
                await bot.edit_message_text(chat_id=channel, message_id=sent_msg.message_id, text=updated_text)
            
            await asyncio.sleep(10)

        if SECTION_CLOSE_STICKER:
            await asyncio.sleep(2)
            await bot.send_sticker(chat_id=channel, sticker=SECTION_CLOSE_STICKER)
        print(f"✅ Session successfully completed for {channel}")
    except Exception as e:
        print(f"Session error in {channel}: {e}")
        
