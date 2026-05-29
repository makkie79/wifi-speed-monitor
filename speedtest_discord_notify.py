"""
Wi-Fi回線速度計測 → Discord通知 + Googleスプレッドシート記録
必要ライブラリ: pip install speedtest-cli requests gspread
"""

import speedtest
import requests
import datetime
import sys
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# ★ 設定ここを編集してください ★
# ==============================
WEBHOOK_URL      = "https://discord.com/api/webhooks/1509847909531648071/p7W_q63H-JqqNE6u9abaItnbn3YH_QSMxG_OR8aCQ9K_uAooD7gbl7V6sSV54RW0s8Sc"
SPREADSHEET_ID   = "1XDkZXA76oThynsRjkSS474g1bGl-GljUubA12IPqqQ0"
CREDENTIALS_FILE = r"C:\Users\maki_e\credentials.json"
# ==============================

def get_ssid() -> str:
    """現在接続中のWi-Fi SSID を取得する"""
    import subprocess
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        for line in result.stdout.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[-1].strip()
                if ssid:
                    return ssid
        return "不明（有線接続の可能性）"
    except Exception:
        return "取得失敗"

def get_location() -> str:
    """IPアドレスから現在地（住所）を取得する"""
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5)
        data = res.json()
        city    = data.get("city", "")
        region  = data.get("region", "")
        country = data.get("country_name", "")
        return f"{country} {region} {city}".strip()
    except Exception:
        return "取得できませんでした"

def measure_speed():
    """回線速度を計測して結果を返す"""
    print("速度計測中...")
    st = speedtest.Speedtest()
    st.get_best_server()
    download_bps = st.download()
    upload_bps = st.upload()
    ping = st.results.ping

    return {
        "download": round(download_bps / 1_000_000, 2),
        "upload":   round(upload_bps   / 1_000_000, 2),
        "ping":     round(ping, 1),
    }

def get_evaluation(dl_mbps: float) -> tuple[str, int]:
    """速度に応じた評価と埋め込みカラーを返す"""
    if dl_mbps >= 100:
        return "🟢 快適", 0x2ECC71
    elif dl_mbps >= 30:
        return "🟡 普通", 0xF1C40F
    elif dl_mbps >= 10:
        return "🟠 やや遅い", 0xE67E22
    else:
        return "🔴 遅い", 0xE74C3C

def save_to_spreadsheet(result: dict, location: str, ssid: str):
    """Googleスプレッドシートに結果を追記する"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SPREADSHEET_ID).sheet1

    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    row = [now, ssid, location, result["download"], result["upload"], result["ping"]]
    sheet.append_row(row)
    print("✅ スプレッドシートに記録しました")

def send_discord_embed(webhook_url: str, result: dict, location: str = "", ssid: str = ""):
    """Discord Webhook でリッチな Embed メッセージを送る"""
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    evaluation, color = get_evaluation(result["download"])

    fields = [
        {"name": "⬇️ ダウンロード", "value": f"**{result['download']} Mbps**", "inline": True},
        {"name": "⬆️ アップロード", "value": f"**{result['upload']} Mbps**", "inline": True},
        {"name": "🏓 Ping",          "value": f"**{result['ping']} ms**",      "inline": True},
        {"name": "総合評価",          "value": evaluation,                      "inline": False},
        {"name": "📶 接続Wi-Fi",     "value": ssid if ssid else "不明",        "inline": True},
        {"name": "📍 大まかな場所",   "value": location if location else "不明", "inline": True},
    ]

    payload = {
        "embeds": [
            {
                "title": "📶 Wi-Fi 速度レポート",
                "color": color,
                "fields": fields,
                "footer": {"text": f"計測日時: {now}"},
            }
        ]
    }

    response = requests.post(webhook_url, json=payload)
    return response.status_code

def main():
    try:
        ssid     = get_ssid()
        location = get_location()
        print(f"接続Wi-Fi: {ssid} / 場所: {location}")
        result = measure_speed()
        print(f"Down: {result['download']} Mbps / Up: {result['upload']} Mbps / Ping: {result['ping']} ms")

        status = send_discord_embed(WEBHOOK_URL, result, location, ssid)
        if status in (200, 204):
            print("✅ Discord に通知を送信しました")
        else:
            print(f"❌ Discord 送信失敗: HTTP {status}", file=sys.stderr)

        save_to_spreadsheet(result, location, ssid)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
