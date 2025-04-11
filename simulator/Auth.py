import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

# 登入帳號密碼
# get it from .env


# 載入 .env 檔案
load_dotenv()

# 讀取環境變數
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")


class Auth:
    def __init__(self):
        self.username = username
        self.password = password
        self.token = None


    def get_token(self):
        # 發送登入請求
        response = requests.post(
            "https://api.worldquantbrain.com/authentication",
            auth=HTTPBasicAuth(username, password)
        )

        # 檢查登入結果
        if response.status_code == 201:
            token = response.headers.get("Set-Cookie", "")
            # 去掉前面兩個字元
            token = token[2:]
            token = token.split(";")[0]

            return token
        else:
            return f"登入失敗：{response.status_code} {response.text}" 
