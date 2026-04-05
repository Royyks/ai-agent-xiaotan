import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 載入環境變數中的 API Key
load_dotenv()
api_key = os.environ.get("YOUTUBE_API_KEY")


if not api_key:
    print("請確保 .env 檔案中有設定 YOUTUBE_API_KEY")
    exit()

youtube = build('youtube', 'v3', developerKey=api_key)

# 你的精華名單 (去除了網址，只保留 Handle 和分類)
channel_data = [
    {"handle": "ompshek", "category": "AI/ Tech"},
    {"handle": "darenge2023", "category": "AI/ Tech"},
    {"handle": "CodeShiba", "category": "AI/ Tech"},
    {"handle": "cwpeng-course", "category": "AI/ Tech"},
    {"handle": "catherinelijs", "category": "AI/ Tech"},
    {"handle": "yologuy", "category": "AI/ Tech"},
    {"handle": "theavocoder", "category": "AI/ Tech"},
    {"handle": "hackbearterry", "category": "AI/ Tech"},
    {"handle": "VolkaEnglish", "category": "English"},
    {"handle": "philosophizethispodcast", "category": "English"},
    {"handle": "hubermanlab", "category": "English"},
    {"handle": "veronikas.languagediaries", "category": "English"},
    {"handle": "bbcnewschinese", "category": "English"},
    {"handle": "25y.retirement", "category": "Finance"},
    {"handle": "ahju", "category": "Finance"},
    {"handle": "阳阳-b2n", "category": "Finance"},
    {"handle": "a2ky9", "category": "Finance"},
    {"handle": "ChattyEnglishStudio", "category": "English"},
    {"handle": "LEP-LearnEnglishPodcast", "category": "English"},
    {"handle": "SpeakEnglishWithClass", "category": "English"},
    {"handle": "dep-daily-english-podcast", "category": "English"},
    {"handle": "kurzgesagt", "category": "English"},
    {"handle": "VoiceTubeTV", "category": "English"},
    {"handle": "jforrestenglish", "category": "English"},
    {"handle": "jpcthk", "category": "AI/ Tech"},
    {"handle": "BBCNews", "category": "News"},
    {"handle": "wsj", "category": "News"},
    {"handle": "letstalk", "category": "English"},
]

final_list = []

print("開始向 YouTube 查詢真實的 Channel ID...")

for item in channel_data:
    handle = item["handle"]
    
    # 關鍵修正：確保 handle 是以 @ 開頭
    formatted_handle = handle if handle.startswith('@') else f"@{handle}"
    
    try:
        # 使用修正後的 formatted_handle
        request = youtube.channels().list(
            part="id,snippet",
            forHandle=formatted_handle
        )
        response = request.execute()
        
        if response.get('items'):
            channel_id = response['items'][0]['id']
            real_title = response['items'][0]['snippet']['title']
            
            # --- 關鍵修改處：將鍵值改為 main.py 預期的名稱 ---
            final_list.append({
                "Channel Name": real_title,     # 原本是 "title"
                "Channel ID": channel_id,       # 原本是 "channel_id"
                "Description": item["category"], # 原本是 "category"
                "Keep": "Yes"                   # 新增這個欄位，並預設為 "Yes"
            })
            # --------------------------------------------
            
            print(f"成功: {formatted_handle} -> {real_title}")
            
    except Exception as e:
         print(f"處理 @{handle} 時發生錯誤: {e}")

# 匯出成最終的 CSV
df = pd.DataFrame(final_list)
df.to_csv('my_youtube_subscriptions.csv', index=False, encoding='utf-8-sig')

print("\n轉換完成！已成功生成 my_youtube_subscriptions.csv")