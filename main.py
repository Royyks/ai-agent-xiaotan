import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

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
    """獲取影片字幕，優先嘗試中文"""
    try:
        # 語言優先順序：繁體中文、簡體中文、英文
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-HK', 'zh-TW', 'zh-CN', 'en'])
        return " ".join([t['text'] for t in transcript_list])
    except Exception:
        # 如果該影片沒有提供字幕，則回傳 None
        return None
    
def ai_assistant_analyze(title, transcript):
    """小探 AI 員工分析邏輯"""
    # 限制字幕長度，避免超出 Token 限制 (Gemini 1.5 Flash 雖然很大，但節省資源是好習慣)
    truncated_transcript = transcript[:10000] 
    
    prompt = f"""
    你是一位專業的事業助理，名字叫「小探」。你的任務是評估 YouTube 影片對我事業的價值。
    我的事業專注於：AI 技術、Web App 開發、以及提升個人效率。

    影片標題：{title}
    影片字幕內容：{truncated_transcript}

    請嚴格依照以下格式回報（請使用繁體中文）：
    1. 【等級評比】：1-5 星（5星為必看）。
    2. 【核心簡報】：用 3 個重點總結影片精華。
    3. 【行動清單】：整理出 3 個對我事業有幫助的具體行動 (Action Items)。
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
            if transcript:
                print(f"  🤖 小探正在分析中...")
                analysis = ai_assistant_analyze(video_title, transcript)
                report_content += f"\n### 來自頻道：{channel_name}\n**影片：{video_title}**\n{analysis}\n---\n"
            else:
                print(f"  ❌ 無法提取字幕，略過分析。")

    # 3. 輸出最終結果
    if report_content:
        print("\n" + "="*20 + " 今日事業簡報 " + "="*20)
        print(report_content)
        # 💡 下一步：在此加入發送 Email 或寫入資料庫的邏輯
    else:
        print("\n📭 今天追蹤的頻道沒有任何新更新。")

if __name__ == "__main__":
    main()