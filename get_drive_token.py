import os
from google_auth_oauthlib.flow import InstalledAppFlow

# 這裡宣告我們需要 Google Drive 的「寫入」權限
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    if not os.path.exists('client_secret.json'):
        print("❌ 找不到 client_secret.json！請確認檔案在同一個資料夾。")
        return

    print("準備開啟瀏覽器授權...")
    # 啟動 OAuth 2.0 授權流程
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # 將授權後的 token 存檔
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("✅ 成功！已生成 token.json，請打開它並複製裡面所有的內容。")

if __name__ == '__main__':
    main()