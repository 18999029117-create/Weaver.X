import sys
import os
import re
import json
import time
import requests

import httpx
from pathlib import Path

# Add parent directory to sys.path to import test_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_data"
TEST_FILE = r"d:\软件集合\网页自动化\AI-Sheet-Pro\tests\test_questions.txt"
REPORT_FILE = r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_report_comprehensive.md"

BASE_URL = "http://127.0.0.1:8000"

class TestClient:
    """后端测试客户端 (Independent Copy)"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=180.0)  # 3分钟超时
    
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
                timeout=300.0 # 5分钟，防止AI思考过久
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ComprehensiveTester:
    def __init__(self):
        self.client = TestClient()
        self.results = []
        
    def parse_questions(self):
        with open(TEST_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split by categories
        raw_sections = re.split(r'((?:第[一二三四五六七]类|Category).*?\(.*?题\).*?\n测试点.*?\n)', content)
        
        parsed_data = []
        current_cat = "General"
        
        for i in range(1, len(raw_sections), 2):
            header = raw_sections[i].strip()
            body = raw_sections[i+1].strip()
            
            # Extract Category Name
            match = re.search(r'[^：:]+', header)
            if match:
                current_cat = header.split('\n')[0]
                
            questions = [q.strip() for q in body.split('\n') if q.strip()]
            
            # Smart Sampling: Take only the 1st question from each category for Quick Verification
            # (User can uncomment to run all 100)
            if questions:
                parsed_data.append({"category": current_cat, "question": questions[0]})
                # parsed_data.append({"category": current_cat, "question": questions[1]}) # Optional: 2nd
                # for q in questions: parsed_data.append({"category": current_cat, "question": q}) # ALL
                
        return parsed_data

    def reset_data_for_category(self, category_str):
        """Based on category text, upload appropriate files"""
        if "数据清洗" in category_str or "Data Cleaning" in category_str or "第一类" in category_str:
            self.client.upload_file(os.path.join(DATA_DIR, "cleaning_data.csv"))
        elif "多表" in category_str or "Multi-table" in category_str or "第二类" in category_str:
            # Upload main files
            self.client.upload_file(os.path.join(DATA_DIR, "employees.csv"))
            self.client.upload_file(os.path.join(DATA_DIR, "departments.csv"))
            # Pre-load others just in case context needs them (DuckDB can handle multi)
            self.client.upload_file(os.path.join(DATA_DIR, "sales_last_month.csv"))
            self.client.upload_file(os.path.join(DATA_DIR, "sales_this_month.csv"))
            self.client.upload_file(os.path.join(DATA_DIR, "stock.csv"))
            self.client.upload_file(os.path.join(DATA_DIR, "prices.csv"))
        else:
            # Default to complex records for Analysis, Filtering, etc.
            self.client.upload_file(os.path.join(DATA_DIR, "sales_records.csv"))

    def run_all(self):
        questions = self.parse_questions()
        total = len(questions)
        print(f"{Colors.HEADER}Found {total} test cases.{Colors.ENDC}")
        
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Comprehensive Test Report\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| ID | Category | Question | Result | Type | Time (s) | TempTable |\n")
            f.write("|---|---|---|---|---|---|---|\n")
        
        success_count = 0
        
        # Cache current category to avoid reloading data every time
        current_cat_signature = ""

        for idx, item in enumerate(questions, 1):
            cat = item['category']
            q = item['question']
            
            print(f"\n{Colors.BOLD}[{idx}/{total}] Assuming category: {cat}{Colors.ENDC}")
            print(f"Query: {q}")
            
            # Reset Data if Category changed (or every ~5 tests to keep fresh)
            if cat != current_cat_signature or idx % 10 == 1:
                print(f"{Colors.OKBLUE}Reloading data context...{Colors.ENDC}")
                self.reset_data_for_category(cat)
                current_cat_signature = cat
                
            start_t = time.time()
            try:
                # Send Query
                resp = self.client.send_query(q)
                duration = round(time.time() - start_t, 2)
                
                success = resp.get('success', False)
                data = resp.get('data', {})
                r_type = data.get('response_type', 'unknown')
                temp_table = data.get('temp_table', '-')
                
                # Check for answer text
                answer = data.get('answer', '')
                if not answer and 'explanation' in data:
                    answer = data['explanation']
                
                # Determine Pass/Fail (Basic)
                # Fail if success=False or type=error
                status = "PASS"
                if not success or r_type == 'error':
                    status = "FAIL"
                else:
                    success_count += 1
                
                # Console Output
                color = Colors.OKGREEN if status == "PASS" else Colors.FAIL
                print(f"{color}Result: {status} ({r_type}){Colors.ENDC}")
                if temp_table != '-':
                    print(f"{Colors.WARNING}Temp Table: {temp_table}{Colors.ENDC}")
                    
                # Write to Report
                with open(REPORT_FILE, "a", encoding="utf-8") as f:
                    # Escape pipes in question/answer
                    safe_q = q.replace("|", "\|")
                    f.write(f"| {idx} | {cat.split()[0]} | {safe_q} | {status} | {r_type} | {duration} | {temp_table} |\n")
                    
            except Exception as e:
                print(f"{Colors.FAIL}Exception: {e}{Colors.ENDC}")
                with open(REPORT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"| {idx} | {cat.split()[0]} | {q} | ERROR | - | - | - |\n")

        print(f"\n{Colors.HEADER}Test Complete. {success_count}/{total} Passed.{Colors.ENDC}")
        print(f"Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_all()
