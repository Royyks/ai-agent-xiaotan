import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

# 1. 初始化與載入設定
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# 設定 YouTube API
youtube = build(
    'youtube', 'v3', developerKey=YOUTUBE_API_KEY
)

def get_recent_videos(channel_id):
    """獲取特定頻道過去 24 小時內的新影片"""
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).isoformat()

    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            publishedAfter=yesterday,
            maxResults=5, # 最多檢查 5 部影片
            order="date",
            type="video"
        )
        response = request.execute()
        return response.get('items', [])
    except Exception as e:
        print(f"查詢頻道 {channel_id} 時出錯: {e}")
        return []
    
def get_transcript(video_id):
    """使用 youtube_transcript_api 獲取影片字幕"""
    try:
        # 優先嘗試抓取中文(繁體/簡體)，若無則抓英文
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-HK', 'zh-TW', 'zh-CN', 'en'])
        return " ".join([t['text'] for t in transcript_list])
    except:
        return None
    
def ai_assistant_analyze(title, transcript):
    """小探 AI 員工的分析邏輯 (模擬 NotebookLM Skill)"""
    prompt = f"""
    你是一位專業的事業助理，名字叫「小探」。你的任務是評估 YouTube 影片對我事業的價值。
    我的事業專注於：AI 技術、Web App 開發、以及提升個人效率。

    影片標題：{title}
    影片字幕內容：{transcript[:15000]}  # 限制長度以節省 Token

    請嚴格依照以下格式回報：
    1. 【等級評比】：1-5 星（5星為必看）。
    2. 【核心簡報】：用 3 個重點總結影片精華。
    3. 【行動清單】：整理出 3 個對我事業有幫助的具體行動 (Action Items)。
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

def main():
    print(f"--- 小探開始工作 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---")
    
    # 讀取斷捨離後的清單
    df = pd.read_csv('my_youtube_subscriptions.csv')
    kept_channels = df[df['Keep'] == 'Yes']
    
    report_content = ""

    for _, row in kept_channels.iterrows():
        channel_name = row['Channel Name']
        channel_id = row['Channel ID']
        
        print(f"正在檢查頻道：{channel_name}...")
        videos = get_recent_videos(channel_id)
        
        for video in videos:
            video_title = video['snippet']['title']
            video_id = video['id']['videoId']
            print(f"  發現新影片：{video_title}")
            
            transcript = get_transcript(video_id)
            if transcript:
                analysis = ai_assistant_analyze(video_title, transcript)
                report_content += f"\n### 來自頻道：{channel_name}\n**影片：{video_title}**\n{analysis}\n---\n"
            else:
                print(f"  (無法提取字幕，略過分析)")

    # 輸出結果 (Step 4 的前哨站)
    if report_content:
        print("\n===== 今日事業簡報 =====")
        print(report_content)
        # 這裡之後會加上發送 Email 的功能
    else:
        print("今天追蹤的頻道沒有更新影片。")

if __name__ == "__main__":
    main()



































# # 這是你的 main.py 檔案內容
# import os
# import pandas as pd
# from dotenv import load_dotenv
# # 假設我們日後會把這兩個功能寫成獨立的函數
# # from youtube_service import get_latest_transcripts
# # from llm_service import evaluate_and_summarize

# def main():
#     print("--- 啟動小探 AI Agent ---")

#     # 步驟 1: 安全地載入 .env 檔案中的 API Keys (僅限本地開發使用)
#     load_dotenv()
#     gemini_key = os.environ.get("GEMINI_API_KEY")
    
#     if not gemini_key:
#         print("錯誤：找不到 GEMINI_API_KEY！")
#         return

#     # 步驟 2: 讀取你整理好的「斷捨離」精華頻道清單
#     csv_file = 'my_youtube_subscriptions.csv'
#     if not os.path.exists(csv_file):
#         print("錯誤：找不到頻道清單，請先執行 get_subscriptions.py")
#         return
        
#     df = pd.read_csv(csv_file)
#     # 過濾出標記為要保留 (Keep='Yes') 的頻道
#     # kept_channels = df[df['Keep'] == 'Yes'] 
#     print(f"成功載入頻道資料庫，準備檢查新影片...")

#     # ==========================================
#     # 以下為邏輯藍圖 (我們接下來要一步步實現的部分)
#     # ==========================================
    
#     # 步驟 3: 檢查這些頻道今天有沒有發佈新影片，並提取字幕
#     # new_videos = get_latest_transcripts(kept_channels)
    
#     # 步驟 4: 將字幕丟給 Gemini 1.5 Pro 進行「等級評比」與「總結」
#     # for video in new_videos:
#     #     analysis_result = evaluate_and_summarize(video.transcript, gemini_key)
        
#     # 步驟 5: 判斷如果價值高於 3 星，整理出 Action Items
#     #         並透過 Google Tasks / Email 通知你
    
#     print("--- 小探今日任務完成 ---")

# if __name__ == "__main__":
#     main()