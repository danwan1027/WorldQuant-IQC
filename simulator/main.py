from Auth import Auth
from Simulator import Simulator
import threading
from concurrent.futures import ThreadPoolExecutor 

if __name__ == "__main__":
    auth = Auth()
    simulator = Simulator(auth)
    simulator.prepare_data()

    # 假設 simulator 和 queue 已經定義
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(len(simulator.queue.queue)):
            future = executor.submit(simulator.simulate)
            futures.append(future)

        # 檢查每個 Future 的結果
        for future in futures:
            try:
                future.result()  # 這會拋出異常（如果有）
            except Exception as e:
                print(f"任務發生錯誤: {e}")

