import requests
import time
import os
from datetime import datetime

# =====================================================================
# CONFIGURATION
# =====================================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
POLL_INTERVAL = 5  
MAX_HISTORY = 60

# Global State
consecutive_losses = 0
total_wins = 0
total_losses = 0
active_prediction = None
last_processed_period = None

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
# HTML FILE EXACT SEED & NUMBER PICKING LOGIC
# =====================================================================
def period_seed(period):
    h = 2166136261
    s = str(period)
    for char in s:
        h ^= ord(char)
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

def pick_numbers_deterministic(history, pool, period, jackpot_mode=False):
    if not pool:
        pool = [5, 6, 7, 8, 9]
    if not history:
        return {"n1": pool[0], "n2": pool[-1]}
    
    rng = mulberry32(period_seed(str(period)) ^ 0x9E3779B9)
    last_num = history[0]
    
    freq = {}
    for n in history[:40]:
        freq[n] = freq.get(n, 0) + 1
        
    last_seen = {}
    for idx, n in enumerate(history):
        if n not in last_seen:
            last_seen[n] = idx
            
    scored = []
    for num in pool:
        score = freq.get(num, 0) * 2
        gap = last_seen.get(num, 60)
        
        if jackpot_mode:
            if gap > 15: score += 80
            elif gap > 8: score += 40
        else:
            if 5 <= gap <= 15: score += 40
            elif 16 <= gap <= 25: score += 25
            elif gap > 25: score += 30
            elif gap <= 1: score -= 15
            
        d = abs(last_num - num)
        if d == 1: score += 18
        if d == 2: score += 10
        
        scored.append({"num": num, "score": score})
        
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    n1 = scored[0]["num"]
    n2 = scored[1]["num"] if len(scored) > 1 else scored[0]["num"]
    
    if n1 == n2:
        alt = next((s["num"] for s in scored if s["num"] != n1), pool[0] if pool[0] != n1 else pool[1])
        n2 = alt
        
    return {"n1": n1, "n2": n2}

# =====================================================================
# PREDICTION ENGINE (Exact HTML Match V59)
# =====================================================================
def analyze_prediction(history, next_period):
    global consecutive_losses
    
    numbers = [int(x["number"]) for x in history[:MAX_HISTORY]]
    types = ["BIG" if n >= 5 else "SMALL" for n in numbers]
    
    if len(types) < 10:
        nums = pick_numbers_deterministic(numbers, [5,6,7,8,9], next_period)
        return {"period": next_period, "type": "BIG", "n1": nums["n1"], "n2": nums["n2"], "confidence": 65, "label": "⏳ TREND START"}

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

    # Target Numbers Pools (Exact HTML match)
    main_pool = [5, 6, 7, 8, 9] if best_side == "BIG" else [0, 1, 2, 3, 4]
    opp_pool = [0, 1, 2, 3, 4] if best_side == "BIG" else [5, 6, 7, 8, 9]

    main_nums = pick_numbers_deterministic(numbers, main_pool, next_period, False)
    opp_nums = pick_numbers_deterministic(numbers, opp_pool, str(next_period) + "opp", False)

    n1 = main_nums["n1"]
    n2 = opp_nums["n1"]
    if n1 == n2:
        alt = next((p for p in opp_pool if p != n1), main_pool[0])
        n2 = alt

    return {
        "period": next_period,
        "type": best_side,
        "n1": n1,
        "n2": n2,
        "confidence": confidence,
        "label": label
    }

# =====================================================================
# MAIN LOOP
# =====================================================================
def main():
    global active_prediction, last_processed_period, consecutive_losses, total_wins, total_losses
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*50)
    print(" 🚀 QUANTUM DEEP PRO V59 — EXACT HTML ENGINE PYTHON")
    print("="*50)
    print(" Status: Connected to Live API...\n")

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
                jackpot = (latest_number == active_prediction["n1"] or latest_number == active_prediction["n2"])
                
                if jackpot:
                    total_wins += 1
                    consecutive_losses = 0
                    status = "💎 JACKPOT WIN"
                    color = "\033[92m"
                elif hit:
                    total_wins += 1
                    consecutive_losses = 0
                    status = "✅ WIN"
                    color = "\033[92m"
                else:
                    total_losses += 1
                    consecutive_losses += 1
                    status = "❌ LOSS"
                    color = "\033[91m"

                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Period: {latest_period[-4:]} | Result: {latest_type} ({latest_number})")
                print(f"   Prediction: {active_prediction['type']} ➔ {active_prediction['n1']}, {active_prediction['n2']} | {color}{status}\033[0m")
                print(f"   Stats: Wins: {total_wins} | Losses: {total_losses} | Loss Streak: {consecutive_losses}")
                
                active_prediction = None

            # 2. GENERATE NEW PREDICTION
            if not active_prediction and last_processed_period != latest_period:
                next_period = str(int(latest_period) + 1)
                
                prediction = analyze_prediction(history, next_period)
                active_prediction = prediction
                last_processed_period = latest_period

                # Format matching HTML copy layout (Last 4 digits or Last 3 digits as per your choice, using last 3/4 digits cleanly)
                p_short = prediction['period'][-3:]  # HTML uses last 3 digits for channel copy
                bold_period = to_bold_unicode(f"PERIOD NO - {p_short}")
                bold_type = to_bold_unicode(prediction['type'])
                bold_nums = to_bold_unicode(f"{prediction['n1']} , {prediction['n2']}")
                
                print("\n" + "-"*50)
                print(f" 🎯 NEW PREDICTION FOR PERIOD: {next_period[-4:]}")
                print(f" 📊 Engine Logic: {prediction['label']} (Conf: {prediction['confidence']}%)")
                print("-" * 50)
                print(" 📋 EXACT COPY FORMAT FOR CHANNEL:")
                print(f" ‼️ {bold_period}")
                print(f" ")
                print(f" 📈 {bold_type} ➔ {bold_nums}")
                print("-" * 50)
                
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
        
