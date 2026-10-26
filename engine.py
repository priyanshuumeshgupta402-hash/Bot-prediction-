import requests
import time
import os
from datetime import datetime
from telegram import Bot
from config import (
    BOT_TOKEN, CHANNEL_USERNAME, WIN_STICKER, 
    JACKPOT_STICKER, SECTION_START_STICKER, SECTION_CLOSE_STICKER
)

# =====================================================================
# CONFIGURATION
# =====================================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
POLL_INTERVAL = 5  # Check every 5 seconds
MAX_HISTORY = 60

bot = Bot(token=BOT_TOKEN)

# Global State
consecutive_losses = 0
total_wins = 0
total_losses = 0
active_prediction = None
last_processed_period = None

# Channel normalizer helper
def normalize_channel(ch_str):
    ch_str = str(ch_str).strip()
    if "t.me/" in ch_str:
        username = ch_str.split("t.me/")[-1].strip('/')
        return f"@{username}"
    if not ch_str.startswith('@') and not ch_str.startswith('-'):
        return f"@{ch_str}"
    return ch_str

CHANNEL = normalize_channel(CHANNEL_USERNAME)

# =====================================================================
# UNICODE BOLD CONVERTER (For WhatsApp/Telegram Copy)
# =====================================================================
def to_bold_unicode(text):
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
        '(': '(', ')': ')', ',': ',', ' ': ' ', '-': '-', '': ''
    }
    return ''.join(bold_map.get(c, c) for c in str(text))

# =====================================================================
# FETCH DATA
# =====================================================================
def fetch_history():
    try:
        response = requests.get(f"{API_URL}?t={int(time.time())}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and "data" in data and "list" in data["data"]:
                return data["data"]["list"]
    except Exception as e:
        print(f"Error fetching data: {e}")
    return []

# =====================================================================
# PREDICTION ENGINE (Strict Size Logic - Tumhari Script)
# =====================================================================
def analyze_prediction(history, next_period):
    global consecutive_losses
    
    numbers = [int(x["number"]) for x in history[:MAX_HISTORY]]
    types = ["BIG" if n >= 5 else "SMALL" for n in numbers]
    
    if len(types) < 10:
        return {"period": next_period, "type": "BIG", "confidence": 65, "label": "⏳ TREND START"}

    size_score = 0
    streak = 1
    for i in range(1, len(types)):
        if types[i] == types[0]:
            streak += 1
        else:
            break
            
    r5 = types[:5].count("BIG") / 5
    r10 = types[:10].count("BIG") / 10
    
    if r5 >= 0.8: size_score += 50
    elif r5 <= 0.2: size_score -= 50
    
    if r10 >= 0.7: size_score += 30
    elif r10 <= 0.3: size_score -= 30
    
    if streak >= 2: 
        size_score += 30 if types[0] == "BIG" else -30

    best_side = "BIG" if size_score >= 0 else "SMALL"
    confidence = min(98, 50 + abs(size_score))

    label = f"🔒 SIZE LOCK — {best_side}"
    
    if consecutive_losses == 1:
        best_side = types[0]  
        confidence = max(88, confidence)
        label = f"⚡ RECOVERY — {best_side}"
    elif consecutive_losses >= 2:
        best_side = types[0]  
        confidence = max(92, confidence)
        label = f"🛡️ HARD SHIELD — {best_side}"

    return {
        "period": next_period,
        "type": best_side,
        "confidence": confidence,
        "label": label
    }

# =====================================================================
# MAIN LOOP (With Telegram Channel Integration)
# =====================================================================
def main():
    global active_prediction, last_processed_period, consecutive_losses, total_wins, total_losses
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*50)
    print(" 🚀 QUANTUM DEEP PRO V60 — TELEGRAM BOT SYNC")
    print("="*50)
    print(f" Status: Connected & Posting to {CHANNEL}...\n")

    while True:
        try:
            history = fetch_history()
            if not history:
                time.sleep(POLL_INTERVAL)
                continue

            latest = history[0]
            latest_period = str(latest["issueNumber"])
            latest_number = int(latest["number"])
            latest_type = "BIG" if latest_number >= 5 else "SMALL"

            # 1. RESOLVE PREVIOUS PREDICTION
            if active_prediction and active_prediction["period"] == latest_period:
                hit = (latest_type == active_prediction["type"])
                
                if hit:
                    total_wins += 1
                    consecutive_losses = 0
                    status = "✅ WIN"
                else:
                    total_losses += 1
                    consecutive_losses += 1
                    status = "❌ LOSS"

                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Period: {latest_period[-4:]} | Result: {latest_type} ({latest_number}) -> {status}")
                active_prediction = None

            # 2. GENERATE AND SEND NEW PREDICTION TO TELEGRAM CHANNEL
            if not active_prediction and last_processed_period != latest_period:
                next_period = str(int(latest_period) + 1)
                
                prediction = analyze_prediction(history, next_period)
                active_prediction = prediction
                last_processed_period = latest_period

                p_short = prediction['period'][-3:]
                bold_period = to_bold_unicode(f"PERIOD NO - {p_short}")
                bold_type = to_bold_unicode(prediction['type'])
                
                # Telegram message formatting
                msg_text = f"‼️ {bold_period}\n\n📈 {bold_type}"
                
                # Send message directly to Telegram channel using bot
                try:
                    bot.send_message(chat_id=CHANNEL, text=msg_text)
                    print(f"✅ Prediction sent to channel {CHANNEL} for period {next_period[-4:]}")
                except Exception as ex:
                    print(f"❌ Failed to send telegram message: {ex}")

                print(f" 🎯 ENGINE PREDICTION: {prediction['type']} (Conf: {prediction['confidence']}%)")
                
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
        
