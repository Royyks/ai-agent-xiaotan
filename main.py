import os
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- 1. 初始化與載入設定 ---
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 檢查關鍵 API Key 是否存在
if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
    print("❌ 錯誤：請確保環境變數中設定了 YOUTUBE_API_KEY 和 GEMINI_API_KEY")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# 設定 YouTube API 服務
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def upload_to_drive(file_path, file_name):
    """將生成的 TXT 檔案上傳至 Google Drive"""
    print(f"☁️ 準備上傳 {file_name} 到 Google Drive...")
    
    # 從環境變數讀取 Service Account 的 JSON 字串與資料夾 ID
    token_json_str = os.getenv("GDRIVE_TOKEN").strip() if os.getenv("GDRIVE_TOKEN") else None
    folder_id = os.getenv("DRIVE_FOLDER_ID")
    
    if not token_json_str or not folder_id:
        print("❌ 錯誤：找不到 GDRIVE_TOKEN 或 DRIVE_FOLDER_ID，跳過上傳。")
        return

    try:
        # 將 JSON 字串轉換為認證物件
        creds_dict = json.loads(token_json_str)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # 建立 Drive API 服務
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # 設定檔案中繼資料 (上傳檔名與目標資料夾)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # 執行上傳
        media = MediaFileUpload(file_path, mimetype='text/plain', resumable=True)
        file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        print(f"✅ 成功！檔案已上傳至 Google Drive (File ID: {file.get('id')})")
    except Exception as e:
        print(f"❌ 上傳 Google Drive 失敗: {e}")

def get_recent_videos(channel_id):
    """獲取特定頻道過去 24 小時內的新影片"""
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).isoformat()

    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            publishedAfter=yesterday,
            maxResults=5, 
            order="date",
            type="video"
        )
        response = request.execute()
        return response.get('items', [])
    except Exception as e:
        print(f"⚠️ 查詢頻道 {channel_id} 時出錯: {e}")
        return []
    
def get_transcript(video_id):
    """增強版：獲取影片字幕，支援自動生成字幕與更多語系"""
    try:
        # 先獲取該影片所有可用的字幕清單
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 擴充語言優先順序 (加入 zh-Hant, zh-Hans, en-US 等)
        langs = ['zh-HK', 'zh-TW', 'zh-Hant', 'zh-CN', 'zh-Hans', 'zh', 'en', 'en-US', 'en-GB']
        
        try:
            # 優先尋找清單中的語言 (這會自動包含創作者手動上傳和 YouTube 自動生成的)
            transcript = transcript_list.find_transcript(langs)
        except:
            # 如果上面指定的語言都沒有，就直接隨便抓清單裡的第一個可用字幕
            transcript = list(transcript_list)[0]
            
        return " ".join([t['text'] for t in transcript.fetch()])
    except Exception:
        # 當影片完全沒有字幕 (例如 Shorts 短影音或創作者關閉字幕) 時會跳到這裡
        return None
    
def ai_assistant_analyze(title, transcript):
    """小探 AI 員工分析邏輯"""
    # 限制字幕長度，避免超出 Token 限制 (Gemini 1.5 Flash 雖然很大，但節省資源是好習慣)
    truncated_transcript = transcript[:10000] 
    
    prompt = f"""
    請精簡總結這部 YouTube 影片對我事業（AI 技術、Web App 開發）的價值。
    
    影片標題：{title}
    影片內容：{truncated_transcript}

    請嚴格使用以下格式輸出（全用繁體中文），不要有額外廢話：
    - 核心總結 1
    - 核心總結 2
    - 行動建議：[具體可執行的行動]
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI 分析失敗: {e}"

def main():
    print(f"--- 🚀 小探開始工作 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---")
    
    # 2. 讀取並清洗 CSV 檔案
    csv_path = 'my_youtube_subscriptions.csv'
    if not os.path.exists(csv_path):
        print(f"❌ 錯誤：找不到 {csv_path}")
        return

    df = pd.read_csv(csv_path)
    
    # 【關鍵修正】：清洗欄位名稱，防止空格或大小寫導致 KeyError
    df.columns = df.columns.str.strip()
    
    # 檢查必要的欄位是否存在
    required_columns = ['Channel ID', 'Keep', 'Channel Name']
    if not all(col in df.columns for col in required_columns):
        print(f"❌ 錯誤：CSV 格式不正確。目前的欄位有: {df.columns.tolist()}")
        print(f"預期需要欄位: {required_columns}")
        return

    # 只處理標記為 'Yes' 的頻道
    kept_channels = df[df['Keep'].str.upper() == 'YES']
    print(f"📊 正在從精華清單中檢查 {len(kept_channels)} 個頻道...")
    
    report_content = ""

    for _, row in kept_channels.iterrows():
        channel_name = row['Channel Name']
        channel_id = row['Channel ID']
        
        print(f"🔍 正在檢查頻道：{channel_name}...")
        videos = get_recent_videos(channel_id)
        
        if not videos:
            print(f"  > 過去 24 小時無更新。")
            continue

        for video in videos:
            video_title = video['snippet']['title']
            video_id = video['id']['videoId']
            print(f"  ✨ 發現新影片：{video_title}")
            
            transcript = get_transcript(video_id)
            
            # --- 1. 判斷是否有字幕，並決定 analysis 變數的內容 ---
            if transcript:
                print(f"  🤖 小探正在分析中...")
                analysis = ai_assistant_analyze(video_title, transcript)
            else:
                print(f"  ❌ 無法提取字幕，略過分析，但仍會記錄。")
                analysis = "⚠️ 無法提取字幕（可能為 Shorts 或未提供），略過 AI 分析。"
            
            # --- 2. 【關鍵修改】：不管有沒有字幕，都將結果寫入 report_content ---
            # 我順便加了影片的 Link，這樣你在 TXT 檔裡可以直接點擊觀看
            report_content += f"Channel: {channel_name}\n"
            report_content += f"Title: {video_title}\n"
            report_content += f"Link: https://www.youtube.com/watch?v={video_id}\n"
            report_content += f"Summary:\n{analysis}\n"
            report_content += "-"*40 + "\n\n"

    # 3. 輸出最終結果與上傳
    if report_content:
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"AI_Summary_{date_str}.txt"
        
        # 加上文件標題
        final_text = f"小探今日事業簡報 ({date_str})\n"
        final_text += "="*40 + "\n\n"
        final_text += report_content
        
        # 將結果寫入本地 TXT 檔
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_text)
            
        print(f"\n📄 已生成本地文件: {filename}")
        
        # 呼叫上傳函數
        upload_to_drive(filename, filename)
    else:
        print("\n📭 今天追蹤的頻道沒有任何新更新，不上傳文件。")
        

if __name__ == "__main__":
    main()