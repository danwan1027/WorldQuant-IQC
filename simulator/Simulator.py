from Auth import Auth
import requests
import time
from queue import Queue
import pandas as pd
import csv
import os
import numpy as np
import threading

csv_lock = threading.Lock()

class Simulator:
    def __init__(self, auth):
        self.auth = auth
        self.token = auth.get_token()
        self.queue = Queue()

    def convert_numpy_to_python(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_numpy_to_python(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_to_python(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj

    def prepare_data(self):
        df = pd.read_csv('data.csv')
        for i in range(len(df)):
            payload = {
                "type": df.iloc[i]['type'],
                "settings": {
                    "nanHandling": df.iloc[i]['nanHandling'],
                    "instrumentType": df.iloc[i]['instrumentType'],
                    "delay": df.iloc[i]['delay'],
                    "universe": df.iloc[i]['universe'],
                    "truncation": df.iloc[i]['truncation'],
                    "unitHandling": df.iloc[i]['unitHandling'],
                    "testPeriod": df.iloc[i]['testPeriod'],
                    "pasteurization": df.iloc[i]['pasteurization'],
                    "region": df.iloc[i]['region'],
                    "language": df.iloc[i]['language'],
                    "decay": df.iloc[i]['decay'],
                    "neutralization": df.iloc[i]['neutralization'],
                    "visualization": df.iloc[i]['visualization']
                },
                "regular": df.iloc[i]['regular']
            }
            self.queue.put(payload)

    def simulate(self):
        
        url = "https://api.worldquantbrain.com/simulations"

        headers = {
            "Accept": "application/json;version=2.0",
            "Content-Type": "application/json",
            "Origin": "https://platform.worldquantbrain.com",
            "Referer": "https://platform.worldquantbrain.com/",
            "Authorization": f"Bearer {self.token}",
        }

        payload = self.queue.get_nowait()  # 嘗試從隊列中取出項目
        print(payload['regular'])
        payload = self.convert_numpy_to_python(payload)

        response = requests.post(url, headers=headers, json=payload)
        # 顯示結果
        print("已送出 Simulation. Status Code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Raw Response:", response.text)

        
        # 取的模擬結果
        status_url = response.headers.get('Location')
        headers = {
            "Accept": "application/json;version=2.0",
            "Authorization": f"Bearer {self.token}",
        }

        while True:
            response = requests.get(status_url, headers=headers)

            if response.status_code != 200:
                print(f"查詢失敗：{response.status_code}")
                break

            data = response.json()
            print("Data", data)
            print("目前模擬狀態：", data.get("status"))

            if data.get("status") == "COMPLETE":
                print("模擬完成 ✅")
                # 顯示完整結果（可自定）
                print(data)

                # 取得 alpha ID
                alpha_id = data.get("alpha")
                print(f"alpha ID: {alpha_id}")

                # 使用 alpha ID 查詢結果
                alpha_url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
                alpha_response = requests.get(alpha_url, headers=headers)

                if alpha_response.status_code == 200:
                    alpha_data = alpha_response.json()
                    print("策略詳細結果：", alpha_data)
                else:
                    print(f"查詢策略結果失敗，狀態碼：{alpha_response.status_code}")
                break

            elif data.get("status") == "FAILED":
                print("模擬失敗 ❌")
                break

            time.sleep(2.5)  # 根據 Retry-After 等待

        self.to_csv(payload, alpha_id, alpha_data)


    def to_csv(self, payload, alpha_id, alpha_data):
        is_data = alpha_data.get("is", {})
        with csv_lock:
            df = pd.read_csv("results.csv")
            new_row = pd.DataFrame({
                "alpha_link": f"https://platform.worldquantbrain.com/alpha/{alpha_id}",
                "sharpe": [is_data.get("sharpe")],
                "turnover": [is_data.get("turnover") * 100],
                "fitness": [is_data.get("fitness")],
                "returns": [is_data.get("returns") * 100],
                "drawdown": [is_data.get("drawdown") * 100],
                "margin": [is_data.get("margin") * 1000],
                "regular": [payload["regular"]],
                "pnl": [is_data.get("pnl")],
                "bookSize": [is_data.get("bookSize")],
                "longCount": [is_data.get("longCount")],
                "shortCount": [is_data.get("shortCount")],
                "type": [payload["type"]],
                "nanHandling": [payload["settings"]["nanHandling"]],
                "instrumentType": [payload["settings"]["instrumentType"]],
                "delay": [payload["settings"]["delay"]],
                "universe": [payload["settings"]["universe"]],
                "truncation": [payload["settings"]["truncation"]],
                "unitHandling": [payload["settings"]["unitHandling"]],
                "testPeriod": [payload["settings"]["testPeriod"]],
                "pasteurization": [payload["settings"]["pasteurization"]],
                "region": [payload["settings"]["region"]],
                "language": [payload["settings"]["language"]],
                "decay": [payload["settings"]["decay"]],
                "neutralization": [payload["settings"]["neutralization"]],
                "visualization": [payload["settings"]["visualization"]]

            })
            new_df = pd.concat([df, new_row], ignore_index=True)
            new_df.to_csv("results.csv", index=False)

        print("✅ CSV 寫入成功！")