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
    
    # Main Table (Left): 3 rows
    main_df = pd.DataFrame({
        "ID": [1, 2, 3],
        "Name": ["MainItem_A", "MainItem_B", "MainItem_C"]
    })
    main_df.to_csv(os.path.join(DATA_DIR, "main_table.csv"), index=False)
    
    # Attr Table (Right): Matches 1 and 3. Has 4 (extra). Missing 2.
    attr_df = pd.DataFrame({
        "ID": [1, 3, 4],
        "Value": ["Value_1", "Value_3", "Value_4"]
    })
    attr_df.to_csv(os.path.join(DATA_DIR, "attr_table.csv"), index=False)
    
    # 2. Upload
    client = TestClient()
    print("Uploading main_table.csv...")
    print(client.upload_file(os.path.join(DATA_DIR, "main_table.csv")))
    print("Uploading attr_table.csv...")
    print(client.upload_file(os.path.join(DATA_DIR, "attr_table.csv")))
    
    # 3. Query
    query = "左边这个表（main_table）是主表，把右边表（attr_table）里的相关信息填进去，匹配不上的留空。"
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
