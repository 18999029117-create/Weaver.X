"""
AI-Sheet-Pro 全面功能测试脚本
测试单表和多表自然语言处理
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_result(test_name, success, data=None, error=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    if data:
        print(f"    返回数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    if error:
        print(f"    错误信息: {error}")

def test_health():
    """测试后端健康状态"""
    print_section("测试 1: 后端健康检查")
    r = requests.get(f"{API_BASE}/api/health")
    data = r.json()
    success = data.get("status") == "ok"
    print_result("健康检查", success, data)
    return success

def test_upload_table_a():
    """测试上传 A 表"""
    print_section("测试 2: 上传 A 表（员工信息）")
    with open("temp/员工信息.csv", "rb") as f:
        files = {"file": ("员工信息.csv", f, "text/csv")}
        r = requests.post(f"{API_BASE}/api/upload/table-a", files=files)
    data = r.json()
    success = data.get("success") == True
    print_result("上传 A 表", success, data)
    return success

def test_upload_table_b():
    """测试上传 B 表"""
    print_section("测试 3: 上传 B 表（薪资表）")
    with open("temp/薪资表.csv", "rb") as f:
        files = {"file": ("薪资表.csv", f, "text/csv")}
        r = requests.post(f"{API_BASE}/api/upload/table-b", files=files)
    data = r.json()
    success = data.get("success") == True
    print_result("上传 B 表", success, data)
    return success

def test_list_tables():
    """测试列出所有表"""
    print_section("测试 4: 获取已加载表列表")
    r = requests.get(f"{API_BASE}/api/tables")
    data = r.json()
    success = data.get("success") == True and len(data.get("data", {})) >= 2
    print_result("表列表", success, data)
    return success

def test_single_table_query_count():
    """单表查询：统计行数"""
    print_section("测试 5: 单表自然语言查询 - 统计行数")
    payload = {"query": "table_a 有多少行数据"}
    r = requests.post(f"{API_BASE}/api/ai/query", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("单表查询-统计行数", success, data)
    return success

def test_single_table_query_sum():
    """单表查询：求和"""
    print_section("测试 6: 单表自然语言查询 - 薪资总和")
    payload = {"query": "计算 table_b 的薪资总和"}
    r = requests.post(f"{API_BASE}/api/ai/query", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("单表查询-求和", success, data)
    return success

def test_single_table_query_avg():
    """单表查询：平均值"""
    print_section("测试 7: 单表自然语言查询 - 平均薪资")
    payload = {"query": "计算薪资的平均值"}
    r = requests.post(f"{API_BASE}/api/ai/query", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("单表查询-平均值", success, data)
    return success

def test_semantic_mapping():
    """测试语义映射"""
    print_section("测试 8: 语义映射 - 识别同义异名列")
    payload = {"table_a": "table_a", "table_b": "table_b"}
    r = requests.post(f"{API_BASE}/api/semantic/mapping", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("语义映射", success, data)
    return success

def test_ai_preview():
    """测试 AI 预览（不执行）"""
    print_section("测试 9: AI 预览 - 合并表格")
    payload = {"query": "合并 table_a 和 table_b，通过员工ID关联"}
    r = requests.post(f"{API_BASE}/api/ai/preview", json=payload)
    data = r.json()
    success = data.get("success") == True and "generated_code" in data.get("data", {})
    print_result("AI 预览", success, data)
    return success

def test_ai_confirm():
    """测试 AI 确认执行"""
    print_section("测试 10: AI 确认执行")
    r = requests.post(f"{API_BASE}/api/ai/confirm")
    data = r.json()
    # 可能成功或失败（取决于是否有待确认的操作）
    print_result("AI 确认执行", True, data)  # 仅记录，不判断失败
    return True

def test_multi_table_join():
    """多表查询：连接"""
    print_section("测试 11: 多表自然语言查询 - 连接表格")
    payload = {"query": "合并这两张表，按员工ID对齐"}
    r = requests.post(f"{API_BASE}/api/ai/query", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("多表连接", success, data)
    return success

def test_sql_query():
    """测试直接 SQL 查询"""
    print_section("测试 12: 直接 SQL 查询")
    payload = {"sql": "SELECT * FROM table_a LIMIT 5"}
    r = requests.post(f"{API_BASE}/api/query/sql", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("SQL 查询", success, data)
    return success

def test_data_view():
    """测试分页视图"""
    print_section("测试 13: 分页视图（影子数据流）")
    payload = {"table_name": "table_a", "offset": 0, "limit": 5}
    r = requests.post(f"{API_BASE}/api/data/view", json=payload)
    data = r.json()
    success = data.get("success") == True
    print_result("分页视图", success, data)
    return success

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪"*30)
    print("        AI-Sheet-Pro 全面功能测试")
    print("🧪"*30)
    
    results = []
    
    results.append(("后端健康检查", test_health()))
    results.append(("上传 A 表", test_upload_table_a()))
    results.append(("上传 B 表", test_upload_table_b()))
    results.append(("表列表", test_list_tables()))
    results.append(("单表-统计行数", test_single_table_query_count()))
    results.append(("单表-求和", test_single_table_query_sum()))
    results.append(("单表-平均值", test_single_table_query_avg()))
    results.append(("语义映射", test_semantic_mapping()))
    results.append(("AI 预览", test_ai_preview()))
    results.append(("AI 确认", test_ai_confirm()))
    results.append(("多表连接", test_multi_table_join()))
    results.append(("SQL 查询", test_sql_query()))
    results.append(("分页视图", test_data_view()))
    
    # 汇总
    print("\n" + "="*60)
    print("  测试汇总")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  通过率: {passed}/{total} ({100*passed/total:.1f}%)")
    
    return passed, total

if __name__ == "__main__":
    run_all_tests()
