import sys
import os
import json
import time
import httpx
import pandas as pd
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
DATA_DIR = r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_data"

class TestClient:
    """后端测试客户端"""
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=180.0)
    
    def upload_file(self, file_path: str, table_name: str = None) -> dict:
        path = Path(file_path)
        with open(path, 'rb') as f:
            files = {'file': (path.name, f, 'application/octet-stream')}
            data = {'table_name': table_name} if table_name else {}
            try:
                resp = self.client.post(f"{self.base_url}/api/upload", files=files, data=data)
                return resp.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    def send_query(self, query: str) -> dict:
        try:
            resp = self.client.post(f"{self.base_url}/api/ai/query", json={"query": query}, timeout=300.0)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # 1. Generate Data
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    
    # Roster: 5 employees
    roster = pd.DataFrame({
        "EmpID": ["E001", "E002", "E003", "E004", "E005"],
        "Name": ["Alice", "Bob", "Charlie", "David", "Eve"]
    })
    roster.to_csv(os.path.join(DATA_DIR, "roster.csv"), index=False)
    
    # Clock In: Only 3 people (Missing David and Eve)
    clockin = pd.DataFrame({
        "EmpID": ["E001", "E002", "E003"],
        "Time": ["09:00", "09:05", "08:55"]
    })
    clockin.to_csv(os.path.join(DATA_DIR, "clockin.csv"), index=False)
    
    # 2. Upload
    client = TestClient()
    print("Uploading roster.csv...")
    print(client.upload_file(os.path.join(DATA_DIR, "roster.csv")))
    print("Uploading clockin.csv...")
    print(client.upload_file(os.path.join(DATA_DIR, "clockin.csv")))
    
    # 3. Query
    query = "表 1 是花名册，表 2 是打卡记录，帮我找出今天没打卡的人。"
    print(f"\nSending Query: {query}")
    start = time.time()
    resp = client.send_query(query)
    print(f"Time: {time.time()-start:.2f}s")
    
    # 4. Result
    if resp.get('success'):
        data = resp.get('data', {})
        print(f"\n✅ Result Type: {data.get('response_type')}")
        print(f"Answer: {data.get('answer')}")
        if 'temp_table' in data:
            print(f"Temp Table: {data['temp_table']}")
    else:
        print(f"\n❌ Error: {resp.get('error')}")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
