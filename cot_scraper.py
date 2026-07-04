import urllib.request
import urllib.parse
import re
import os

# Konfigurasi dari Environment Variables GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Taktik Backdoor: Ambil data replika teks CFTC resmi dari mirror repositori GitHub publik yang selalu di-update
# Ini memecah masalah blokir 403 karena kita mengunduh dari server GitHub ke GitHub
CFTC_MIRROR_URL = "https://raw.githubusercontent.com/jmerle/cftc-cot-data/master/data/legacy_futures/comex.txt"

def send_telegram_message(message):
    payload = f"chat_id={CHAT_ID}&text={urllib.parse.quote(message)}&parse_mode=Markdown"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?{payload}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        urllib.request.urlopen(req)
        print("Pesan berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Gagal mengirim pesan ke Telegram: {e}")

def parse_cot_data():
    try:
        print("Mengunduh data CFTC via Jalur Belakang GitHub Mirror...")
        
        # Unduh data dari repositori cftc-cot-data (Mirror terpercaya)
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(CFTC_MIRROR_URL, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
        
        # Cari blok data GOLD paling terbaru di dalam file
        pattern = r"(GOLD - COMMODITY EXCHANGE INC\..*?)(?=\n\n|\Z)"
        matches = list(re.finditer(pattern, html, re.DOTALL | re.IGNORECASE))
        
        if not matches:
            return "Data GOLD tidak ditemukan di dalam file cftc-mirror GitHub."
            
        # Ambil entri paling akhir (terbaru) di file mirror
        last_match = matches[-1]
        block_text = last_match.group(1)
        lines = block_text.split('\n')
        
        date_info = lines[1].strip() if len(lines) > 1 else "Terbaru"
        
        # Ekstrak baris angka "All" dan "Changes"
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
        
        # Hitung Analisis Kuantitatif Net Position
        net_position = long_pos - short_pos
        sentiment = "🟢 BULLISH" if net_position > 0 else "🔴 BEARISH"
        
        report = (
            f"📊 *LAPORAN COT EMAS (GOLD) - ANTI BLOKIR*\n"
            f"📅 _Laporan: {date_info}_\n"
            f"=============================\n"
            f"🔹 *Open Interest:* {open_interest:,}\n\n"
            f"👤 *Non-Commercial (Big Money):*\n"
            f"  • Long (Buy): {long_pos:,} (Chg: {change_long:+:,})\n"
            f"  • Short (Sell): {short_pos:,} (Chg: {change_short:+:,})\n"
            f"  • *Net Position:* {net_position:,}\n\n"
            f"🔥 *Sentimen Pasar:* {sentiment}\n"
            f"=============================\n"
            f"🚀 _Sistem sukses menembus pertahanan via GitHub Mirror!_"
        )
        return report

    except Exception as e:
        return f"Terjadi error saat parsing data Mirror: {str(e)}"

if __name__ == "__main__":
    report_message = parse_cot_data()
    send_telegram_message(report_message)
