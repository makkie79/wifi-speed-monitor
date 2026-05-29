# 📶 Wi-Fi Speed Monitor

Wi-Fiの回線速度を定期的に自動計測し、Discordへ通知・Googleスプレッドシートへ記録するツールです。

## 機能

- 3時間ごとに自動でWi-Fi速度を計測（Windowsタスクスケジューラ使用）
- 接続中のWi-Fi SSID を自動取得
- IPアドレスから大まかな場所を自動取得
- Discord Webhook でリッチな通知を送信
- Google スプレッドシートに計測結果を自動追記

## 通知イメージ

```
📶 Wi-Fi 速度レポート
⬇️ ダウンロード   ⬆️ アップロード   🏓 Ping
382.90 Mbps       234.48 Mbps       5.6 ms
総合評価: 🟢 快適
📶 接続Wi-Fi: HomeWiFi
📍 大まかな場所: Japan Tokyo Shinjuku
計測日時: 2026/05/29 09:00
```

## 必要環境

- Windows PC
- Python 3.x
- 以下のライブラリ

```
pip install speedtest-cli requests gspread google-auth
```

## セットアップ

### 1. Discord Webhook URL の取得
1. Discordで通知を受け取りたいチャンネルを右クリック
2. 「チャンネルの編集」→「連携サービス」→「ウェブフック」
3. 「新しいウェブフック」→「ウェブフックURLをコピー」

### 2. Google Sheets API の設定
1. [Google Cloud Console](https://console.cloud.google.com) でプロジェクトを作成
2. Google Sheets API を有効化
3. サービスアカウントを作成してJSON鍵ファイルをダウンロード
4. スプレッドシートをサービスアカウントのメールアドレスと共有（編集者権限）

### 3. スクリプトの設定
`speedtest_discord_notify.py` を開いて以下の3箇所を編集：

```python
WEBHOOK_URL      = "DiscordのWebhook URLを貼り付け"
SPREADSHEET_ID   = "スプレッドシートIDを貼り付け"
CREDENTIALS_FILE = r"C:\Users\ユーザー名\credentials.json"
```

### 4. タスクスケジューラへの登録（3時間ごとの自動実行）
管理者としてコマンドプロンプトを開いて実行：

```
schtasks /create /tn "WiFiSpeedNotify" /tr "python C:\Users\ユーザー名\speedtest_discord_notify.py" /sc hourly /mo 3 /st 08:00 /ru "ユーザー名" /rl HIGHEST /f
```

## 自動実行の停止・再開

```bash
# 停止
schtasks /change /tn "WiFiSpeedNotify" /disable

# 再開
schtasks /change /tn "WiFiSpeedNotify" /enable
```

## スプレッドシートの列構成

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| 日時 | SSID | 場所 | ダウンロード(Mbps) | アップロード(Mbps) | Ping(ms) |

## 注意事項

- `credentials.json` はGitHubにアップロードしないでください（`.gitignore` で除外済み）
- Discord Webhook URLも外部に公開しないでください
- PCの電源が入っている間のみ自動実行されます
