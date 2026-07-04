import requests
import re
import os

# Konfigurasi dari Environment Variables GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Menggunakan Jina AI Reader sebagai Bouncer/Bypass IP
JINA_READER_URL = "https://r.jina.ai/https://www.cftc.gov/dea/options/deacmxlof.htm"

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

def parse_cot_data():
    try:
        print("Mengambil data CFTC via Jina AI Reader...")
        response = requests.get(JINA_READER_URL, timeout=30)
        
        if response.status_code != 200:
            return f"Jina AI Reader gagal merespons. Status: {response.status_code}"
            
        markdown_text = response.text
        
        # Cari blok data GOLD menggunakan Regex
        pattern = r"(GOLD - COMMODITY EXCHANGE INC\..*?)(?=\n\n|\Z)"
        match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return "Data GOLD tidak ditemukan di output Jina Reader."
            
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
        
        # FIX KUNCI: Ubah ke float dulu sebelum dikonversi ke int agar kebal error desimal '75.5'
        open_interest = int(float(numbers[1].replace(',', '')))
        long_pos = int(float(numbers[2].replace(',', '')))
        short_pos = int(float(numbers[3].replace(',', '')))
        
        change_long = int(float(change_numbers[1].replace(',', '')))
        change_short = int(float(change_numbers[2].replace(',', '')))
        
        # Hitung Analisis Kuantitatif Net Position
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
            f"⚡ _Bypass Sukses & Konversi Angka Desimal Sempurna!_"
        )
        return report

    except Exception as e:
        return f"Terjadi error saat parsing data: {str(e)}"

if __name__ == "__main__":
    report_message = parse_cot_data()
    send_telegram_message(report_message)
