import urllib.request
import re
import os

# Konfigurasi dari Environment Variables GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# URL Data Mentah Legacy Futures Only untuk bursa COMEX/CME
CFTC_URL = "https://www.cftc.gov/dea/futures/deacmxas.htm"

def send_telegram_message(message):
    payload = f"chat_id={CHAT_ID}&text={urllib.parse.quote(message)}&parse_mode=Markdown"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?{payload}"
    try:
        urllib.request.urlopen(url)
        print("Pesan berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Gagal mengirim pesan: {e}")

def parse_cot_data():
    try:
        # 1. Download data mentah
        with urllib.request.urlopen(CFTC_URL) as response:
            html = response.read().decode('utf-8')
        
        # 2. Cari blok data GOLD menggunakan Regex
        # Mengambil teks dari kata "GOLD" sampai garis pembatas berikutnya
        pattern = r"(GOLD - COMMODITY EXCHANGE INC\..*?)(?=\n\n|\Z)"
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return "Data GOLD tidak ditemukan di file CFTC terbaru."
            
        block_text = match.group(1)
        lines = block_text.split('\n')
        
        # 3. Ekstrak baris angka "All" dan "Changes"
        # Baris "All" biasanya ada di indeks ke-7 atau ke-8 dalam blok teks
        all_line = ""
        changes_line = ""
        for line in lines:
            if line.startswith("All  :"):
                all_line = line
            if "Changes in Commitments from:" in line:
                # Ambil baris tepat di bawah tulisan Changes
                idx = lines.index(line)
                changes_line = lines[idx+1]
        
        # Ekstrak angka menggunakan regex dari baris "All"
        # Format baris All: All  :   Open_Int:   Long   Short   Spreading ...
        numbers = re.findall(r'[\d,.-]+', all_line)
        change_numbers = re.findall(r'[\d,.-]+', changes_line)
        
        # Bersihkan koma pada angka
        open_interest = int(numbers[1].replace(',', ''))
        long_pos = int(numbers[2].replace(',', ''))
        short_pos = int(numbers[3].replace(',', ''))
        
        change_long = int(change_numbers[1].replace(',', ''))
        change_short = int(change_numbers[2].replace(',', ''))
        
        # 4. Hitung Analisis Kuantitatif
        net_position = long_pos - short_pos
        sentiment = "🟢 BULLISH" if net_position > 0 else "🔴 BEARISH"
        
        # 5. Susun Pesan Telegram
        report = (
            f"📊 *LAPORAN COT EMAS (GOLD) TERBARU*\n"
            f"=============================\n"
            f"🔹 *Open Interest:* {open_interest:,}\n\n"
            f"👤 *Non-Commercial (Big Money):*\n"
            f"  • Long (Buy): {long_pos:,} (Chg: {change_long:+:,})\n"
            f"  • Short (Sell): {short_pos:,} (Chg: {change_short:+:,})\n"
            f"  • *Net Position:* {net_position:,}\n\n"
            f"🔥 *Sentimen Pasar:* {sentiment}\n"
            f"=============================\n"
            f"💡 _Data ini mencerminkan posisi raksasa Wall Street per hari Selasa lalu._"
        )
        return report

    except Exception as e:
        return f"Terjadi error saat parsing data: {str(e)}"

if __name__ == "__main__":
    report_message = parse_cot_data()
    send_telegram_message(report_message)
