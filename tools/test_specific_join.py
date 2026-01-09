import sys
import os
import json
import time
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

class TestClient:
    """后端测试客户端 (Independent Copy)"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=180.0)
    
    def upload_file(self, file_path: str, table_name: str = None) -> dict:
        """上传文件"""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在: {file_path}"}
        
        with open(path, 'rb') as f:
            files = {'file': (path.name, f, 'application/octet-stream')}
            data = {'table_name': table_name} if table_name else {}
            try:
                resp = self.client.post(
                    f"{self.base_url}/api/upload",
                    files=files,
                    data=data
                )
                return resp.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    def send_query(self, query: str) -> dict:
        """发送 AI 查询"""
        try:
            resp = self.client.post(
                f"{self.base_url}/api/ai/query",
                json={"query": query},
                timeout=300.0
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    client = TestClient()
    print("Uploading employees.csv...")
    print(client.upload_file(r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_data\employees.csv"))
    print("Uploading departments.csv...")
    print(client.upload_file(r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_data\departments.csv"))
    
    query = "帮我根据“员工ID”，把表 2 里的“部门名称”匹配到表 1 里来。"
    print(f"\nSending Query: {query}")
    start = time.time()
    resp = client.send_query(query)
    print(f"Time: {time.time()-start:.2f}s")
    
    # Print logic
    if resp.get('success'):
        data = resp.get('data', {})
        print(f"\n✅ Result Type: {data.get('response_type')}")
        print(f"Answer: {data.get('answer')}")
        if 'temp_table' in data:
            print(f"Temp Table: {data['temp_table']}")
            # Ideally fetch preview of temp table to confirm column added?
            # But just existence is good.
    else:
        print(f"\n❌ Error: {resp.get('error')}")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
