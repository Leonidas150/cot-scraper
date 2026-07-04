import urllib.request
import urllib.parse
import zipfile
import io
import re
import os

# Konfigurasi dari Environment Variables GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# URL Data Mentah ZIP
CFTC_ZIP_URL = "https://www.cftc.gov/files/dea/history/deahist2026.zip"

# LIST PRIVATE PROXY LU
# Dipecah menjadi dict agar mudah diproses oleh sistem autentikasi urllib
PRIVATE_PROXIES = [
    {"ip": "31.59.20.176", "port": "6754", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "31.56.127.193", "port": "7684", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "45.38.107.97", "port": "6014", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "38.154.203.95", "port": "5863", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "198.105.121.200", "port": "6462", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "64.137.96.74", "port": "6641", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "198.23.243.226", "port": "6361", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "38.154.185.97", "port": "6370", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "142.111.67.146", "port": "5611", "user": "epefkxqk", "pass": "cgq4onvt02dz"},
    {"ip": "191.96.254.138", "port": "6185", "user": "epefkxqk", "pass": "cgq4onvt02dz"}
]

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

def fetch_data_with_private_proxy():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # 1. Coba koneksi langsung dulu
    try:
        print("Mencoba koneksi langsung...")
        req = urllib.request.Request(CFTC_ZIP_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Koneksi langsung ditolak/gagal. Mengalihkan ke Private Proxy...")

    # 2. Loop melalui list private proxy lu jika koneksi langsung gagal
    for p in PRIVATE_PROXIES:
        proxy_url = f"http://{p['user']}:{p['pass']}@{p['ip']}:{p['port']}"
        try:
            print(f"Mencoba private proxy: {p['ip']}:{p['port']}")
            
            # Setup proxy handler dengan kredensial login tersemat di URL proxy
            proxy_support = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_support)
            opener.addheaders = [('User-Agent', headers['User-Agent'])]
            
            # Eksekusi unduhan
            with opener.open(CFTC_ZIP_URL, timeout=12) as response:
                data = response.read()
                print(f"🚀 BOOM! Sukses nembus pakai Private Proxy: {p['ip']}")
                return data
        except Exception as proxy_error:
            print(f"Proxy {p['ip']} gagal: {proxy_error}. Mencoba list berikutnya...")
            continue
            
    raise Exception("Seluruh Private Proxy sudah dicoba dan gagal menembus target.")

def parse_cot_data():
    try:
        # Ambil data menggunakan taktik private proxy terbaru
        zip_data = fetch_data_with_private_proxy()
            
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            file_name = z.namelist()[0]
            html = z.read(file_name).decode('utf-8')
        
        pattern = r"(GOLD - COMMODITY EXCHANGE INC\..*?)(?=\n\n|\Z)"
        matches = list(re.finditer(pattern, html, re.DOTALL | re.IGNORECASE))
        
        if not matches:
            return "Data GOLD tidak ditemukan di dalam file arsip CFTC."
            
        last_match = matches[-1]
        block_text = last_match.group(1)
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
            f"📊 *LAPORAN COT EMAS (GOLD) - PREMIUM PROXY*\n"
            f"📅 _Laporan: {date_info}_\n"
            f"=============================\n"
            f"🔹 *Open Interest:* {open_interest:,}\n\n"
            f"👤 *Non-Commercial (Big Money):*\n"
            f"  • Long (Buy): {long_pos:,} (Chg: {change_long:+:,})\n"
            f"  • Short (Sell): {short_pos:,} (Chg: {change_short:+:,})\n"
            f"  • *Net Position:* {net_position:,}\n\n"
            f"🔥 *Sentimen Pasar:* {sentiment}\n"
            f"=============================\n"
            f"🔒 _Bypass Aman Menggunakan Jaringan Private Proxy._"
        )
        return report

    except Exception as e:
        return f"Terjadi error saat parsing data: {str(e)}"

if __name__ == "__main__":
    report_message = parse_cot_data()
    send_telegram_message(report_message)
