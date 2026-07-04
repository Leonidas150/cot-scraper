
import requests
import re
import os

# Konfigurasi dari Environment Variables GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# URL VALID DARI LU
CFTC_URL = "https://www.cftc.gov/dea/options/deacmxlof.htm"

# LIST PRIVATE PROXY LU (Format yang dimengerti library requests)
# Disamain persis kayak skema curl -x lu tadi
PRIVATE_PROXIES = [
    "http://epefkxqk:cgq4onvt02dz@31.59.20.176:6754",
    "http://epefkxqk:cgq4onvt02dz@31.56.127.193:7684",
    "http://epefkxqk:cgq4onvt02dz@45.38.107.97:6014",
    "http://epefkxqk:cgq4onvt02dz@38.154.203.95:5863",
    "http://epefkxqk:cgq4onvt02dz@198.105.121.200:6462",
    "http://epefkxqk:cgq4onvt02dz@64.137.96.74:6641",
    "http://epefkxqk:cgq4onvt02dz@198.23.243.226:6361",
    "http://epefkxqk:cgq4onvt02dz@38.154.185.97:6370",
    "http://epefkxqk:cgq4onvt02dz@142.111.67.146:5611",
    "http://epefkxqk:cgq4onvt02dz@191.96.254.138:6185"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("Pesan berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Gagal mengirim pesan ke Telegram: {e}")

def fetch_data_like_curl():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Loop nyobain proxy satu per satu pake engine requests (setara curl)
    for proxy in PRIVATE_PROXIES:
        proxy_config = {
            "http": proxy,
            "https": proxy
        }
        try:
            print(f"Mencoba nembus via proxy (Curl Mode): {proxy.split('@')[-1]}")
            # requests.get otomatis nanganin SSL/TLS tunneling dengan bener lewat proxy
            response = requests.get(CFTC_URL, headers=headers, proxies=proxy_config, timeout=12)
            
            if response.status_code == 200:
                print("🚀 BOOM! Sukses ambil data pake Requests ala Curl!")
                return response.text
            else:
                print(f"Proxy merespons tapi status code: {response.status_code}")
        except Exception as e:
            print(f"Proxy gagal merespons: {e}")
            continue
            
    raise Exception("Seluruh Proxy premium lu gagal diproses oleh sistem.")

def parse_cot_data():
    try:
        html = fetch_data_like_curl()
        
        # Cari blok data GOLD menggunakan Regex
        pattern = r"(GOLD - COMMODITY EXCHANGE INC\..*?)(?=\n\n|\Z)"
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return "Data GOLD tidak ditemukan di halaman web CFTC."
            
        block_text = match.group(1)
        lines = block_text.split('\n')
        
        date_info = lines[1].strip() if len(lines) > 1 else "Terbaru"
        
        all_line = ""
        changes_line = ""
        for line in lines:
            if line.startswith("All  :"):
                all_line = line
            if "Changes in Commitments from:" in line:
                idx = lines.index(line)
                changes_line = lines[idx+1]
        
        numbers = re.findall(r'[\d,.-]+', all_line)
        change_numbers = re.findall(r'[\d,.-]+', changes_line)
        
        open_interest = int(numbers[1].replace(',', ''))
        long_pos = int(numbers[2].replace(',', ''))
        short_pos = int(numbers[3].replace(',', ''))
        
        change_long = int(change_numbers[1].replace(',', ''))
        change_short = int(change_numbers[2].replace(',', ''))
        
        net_position = long_pos - short_pos
        sentiment = "🟢 BULLISH" if net_position > 0 else "🔴 BEARISH"
        
        report = (
            f"📊 *LAPORAN COT EMAS (GOLD) TERBARU*\n"
            f"📅 _Laporan: {date_info}_\n"
            f"=============================\n"
            f"🔹 *Open Interest:* {open_interest:,}\n\n"
            f"👤 *Non-Commercial (Big Money):*\n"
            f"  • Long (Buy): {long_pos:,} (Chg: {change_long:+:,})\n"
            f"  • Short (Sell): {short_pos:,} (Chg: {change_short:+:,})\n"
            f"  • *Net Position:* {net_position:,}\n\n"
            f"🔥 *Sentimen Pasar:* {sentiment}\n"
            f"=============================\n"
            f"💡 _Bypass HTTPS Proxy via Requests Sukses Total!_"
        )
        return report

    except Exception as e:
        return f"Terjadi error saat parsing data: {str(e)}"

if __name__ == "__main__":
    report_message = parse_cot_data()
    send_telegram_message(report_message)
