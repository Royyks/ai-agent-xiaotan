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
]

final_list = []

print("開始向 YouTube 查詢真實的 Channel ID...")

for item in channel_data:
    handle = item["handle"]
    try:
        # 使用 forHandle endpoint 查詢頻道資訊
        request = youtube.channels().list(
            part="id,snippet",
            forHandle=handle
        )
        response = request.execute()
        
        if response['items']:
            channel_info = response['items'][0]
            real_id = channel_info['id']
            real_title = channel_info['snippet']['title']
            
            final_list.append({
                'Channel Name': real_title,
                'Channel ID': real_id,
                'Description': item['category'], # 我們把 Description 替換成你的分類
                'Keep': 'Yes'
            })
            print(f"成功: @{handle} -> {real_title} ({real_id})")
        else:
            print(f"警告: 找不到 @{handle} 的頻道資訊")
            
    except Exception as e:
         print(f"處理 @{handle} 時發生錯誤: {e}")

# 匯出成最終的 CSV
df = pd.DataFrame(final_list)
df.to_csv('my_youtube_subscriptions.csv', index=False, encoding='utf-8-sig')

print("\n轉換完成！已成功生成 my_youtube_subscriptions.csv")