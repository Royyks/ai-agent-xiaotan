import os
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 定義我們需要的權限範圍 (Scope)：只需要唯讀權限
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def authenticate_youtube():
    """處理 OAuth 2.0 登入流程"""
    creds = None
    # 這裡會讀取你剛才下載的 JSON 檔案
    if os.path.exists('client_secret.json'):
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', SCOPES)
        # 執行時會彈出瀏覽器要求你登入 Google 帳號
        creds = flow.run_local_server(port=0)
    else:
        print("找不到 client_secret.json，請確認檔案位置。")
        exit()
    
    # 建立 YouTube API 服務物件
    youtube = build('youtube', 'v3', credentials=creds)
    return youtube

def get_all_subscriptions(youtube):
    """呼叫 subscriptions.list 獲取所有訂閱頻道"""
    subscriptions = []
    next_page_token = None

    print("開始獲取訂閱清單...")
    while True:
        # 這是核心的 API 呼叫 (Endpoint)
        request = youtube.subscriptions().list(
            part="snippet", # 我們只需要 snippet (包含頻道名稱、描述等)
            mine=True,      # 代表獲取「我的」訂閱
            maxResults=50,  # 每次拉取最大值 50
            pageToken=next_page_token
        )
        response = request.execute()

        # 解析回傳的 JSON 資料
        for item in response.get('items', []):
            channel_title = item['snippet']['title']
            channel_id = item['snippet']['resourceId']['channelId']
            
            subscriptions.append({
                'Channel Name': channel_title,      # 統一用大寫開頭與空格
                'Channel ID': channel_id,          # 統一用大寫開頭與空格
                'Description': 'Pending Review',    # 預設文字
                'Keep': 'Yes'                      # 預設為 Yes，這樣如果你不手動改，小探也會幫你爬
            })

        # 檢查是否有下一頁
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return subscriptions

if __name__ == "__main__":
    yt_service = authenticate_youtube()
    subs_data = get_all_subscriptions(yt_service)
    
    # 使用 Pandas 將資料轉換為 DataFrame 並儲存為 CSV
    df = pd.DataFrame(subs_data)
    df.to_csv('my_youtube_subscriptions.csv', index=False, encoding='utf-8-sig')
    
    print(f"成功！已將 {len(subs_data)} 個訂閱頻道匯出至 my_youtube_subscriptions.csv")