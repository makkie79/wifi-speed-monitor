"""
面接評価データ → Claude AI分析 → Discord通知スクリプト
必要ライブラリ: pip install gspread google-auth anthropic
"""

import gspread
from google.oauth2.service_account import Credentials
import anthropic
import requests
import datetime
import sys

# ==============================
# ★ 設定は外部「.env」ファイルを参照 ★
# ==============================
import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\maki_e\.env")

SPREADSHEET_ID    = "1gprRzNJpWpemkN4hn8pwxob-4QFVl3Aaxo5BjCEoi3o"
CREDENTIALS_FILE  = r"C:\Users\maki_e\credentials.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBHOOK_URL       = os.getenv("DISCORD_WEBHOOK_URL")
# ==============================

def get_latest_interview() -> dict | None:
    """スプレッドシートから最新の面接データを1件取得する"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SPREADSHEET_ID).sheet1

    rows = sheet.get_all_records()
    if not rows:
        print("データがありません")
        return None

    latest = rows[-1]
    # キー名の前後スペースをすべて除去して扱いやすくする
    cleaned = {k.strip(): v for k, v in latest.items()}
    return cleaned

def analyze_with_claude(data: dict) -> str:
    """Anthropic APIで面接データを分析してサマリーを生成する"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
以下は面接評価データです。採用担当マネージャーへの簡潔な報告文を日本語で作成してください。

【候補者名】{data.get('候補者名', '不明')}
【応募職種】{data.get('応募職種', '不明')}
【面接日】{data.get('面接日', '不明')}
【面接担当者】{data.get('面接担当者名', '不明')}

【評価スコア（5点満点）】
・コミュニケーション力：{data.get('コミュニケーション力', '不明')}点
・志望動機の強さ：{data.get('志望動機の強さ', '不明')}点
・論理的思考力：{data.get('論理的思考力', '不明')}点
・即戦力度：{data.get('即戦力度', '不明')}点
・カルチャーフィット：{data.get('カルチャーフィット', '不明')}点

【強みと感じた点】{data.get('強みと感じた点', 'なし')}
【懸念点】{data.get('懸念点', 'なし')}
【総合コメント】{data.get('総合コメント', 'なし')}
【採用推薦】{data.get('採用推薦', '不明')}

以下の形式で報告文を作成してください：
1. 総合評価（平均スコアと一言評価）
2. 主な強み（2〜3点）
3. 懸念事項（あれば）
4. 推薦判定と理由
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def send_discord(webhook_url: str, data: dict, summary: str):
    """Discord Webhookに面接サマリーを送る"""
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    recommendation = data.get('採用推薦', '')
    if recommendation == '推薦する':
        color = 0x2ECC71
        emoji = "🟢"
    elif recommendation == '保留':
        color = 0xF1C40F
        emoji = "🟡"
    else:
        color = 0xE74C3C
        emoji = "🔴"

    payload = {
        "embeds": [
            {
                "title": f"📋 面接評価レポート　{emoji} {recommendation}",
                "color": color,
                "fields": [
                    {"name": "👤 候補者名", "value": str(data.get('候補者名', '不明')), "inline": True},
                    {"name": "💼 応募職種", "value": str(data.get('応募職種', '不明')), "inline": True},
                    {"name": "📅 面接日",   "value": str(data.get('面接 日', '不明')),  "inline": True},
                    {"name": "🤖 AI分析サマリー", "value": summary[:1000], "inline": False},
                ],
                "footer": {"text": f"通知日時: {now}"}
            }
        ]
    }

    response = requests.post(webhook_url, json=payload)
    return response.status_code

def main():
    try:
        print("最新の面接データを取得中...")
        data = get_latest_interview()
        if not data:
            sys.exit(0)

        print(f"候補者: {data.get('候補者名')} / 推薦: {data.get('採用推薦')}")
        print(f"取得したキー一覧: {list(data.keys())}")

        print("Claude AIで分析中...")
        summary = analyze_with_claude(data)
        print("分析完了！")

        status = send_discord(WEBHOOK_URL, data, summary)
        if status in (200, 204):
            print("✅ Discordに通知を送信しました")
        else:
            print(f"❌ Discord送信失敗: HTTP {status}", file=sys.stderr)

    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
