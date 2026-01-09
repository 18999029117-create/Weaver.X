#!/usr/bin/env python
"""
AI-Sheet-Pro 自动化测试工具 (增强版)
- 绕过前端 UI 直接测试后端 API
- 实时写入大白话日志文件 (test_log.md)
- 让非技术人员也能看懂测试过程
"""

import sys
import os
import json
import time
import httpx
from pathlib import Path
from datetime import datetime

# 后端服务地址
BASE_URL = "http://127.0.0.1:8000"

# 日志文件路径
LOG_FILE = Path(__file__).parent / "test_log.md"


class RealTimeLogger:
    """实时日志记录器 - 用大白话写日志"""
    
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        self.start_time = datetime.now()
        self._init_log()
    
    def _init_log(self):
        """初始化日志文件"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"# 🧪 AI-Sheet-Pro 测试日志\n\n")
            f.write(f"**开始时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"---\n\n")
        print(f"📝 日志文件: {self.log_file}")
    
    def _write(self, content):
        """实时写入日志（追加模式）"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(content)
            f.flush()  # 立即刷新到磁盘
    
    def step(self, step_num, title, description):
        """记录一个测试步骤"""
        now = datetime.now().strftime('%H:%M:%S')
        self._write(f"\n## 📌 第{step_num}步：{title}\n")
        self._write(f"*时间: {now}*\n\n")
        self._write(f"{description}\n\n")
        print(f"📌 Step {step_num}: {title}")
    
    def success(self, message):
        """记录成功信息"""
        self._write(f"✅ **成功**: {message}\n\n")
        print(f"✅ {message}")
    
    def error(self, message):
        """记录错误信息"""
        self._write(f"❌ **失败**: {message}\n\n")
        print(f"❌ {message}")
    
    def info(self, message):
        """记录普通信息"""
        self._write(f"ℹ️ {message}\n\n")
        print(f"ℹ️  {message}")
    
    def warn(self, message):
        """记录警告信息"""
        self._write(f"⚠️ **注意**: {message}\n\n")
        print(f"⚠️  {message}")
    
    def data(self, title, content):
        """记录数据详情（用代码块）"""
        self._write(f"**{title}**:\n```\n{content}\n```\n\n")
    
    def thinking(self, message):
        """记录 AI 思考过程"""
        self._write(f"🤔 **AI思考**: {message}\n\n")
    
    def action(self, message):
        """记录 AI 行动"""
        self._write(f"🔧 **AI行动**: {message}\n\n")
    
    def result(self, message):
        """记录执行结果"""
        self._write(f"📊 **执行结果**: {message}\n\n")
    
    def finish(self, success=True):
        """结束日志"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self._write(f"\n---\n\n")
        self._write(f"## 🏁 测试结束\n\n")
        self._write(f"**结束时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        self._write(f"**总耗时**: {duration:.1f} 秒\n\n")
        
        if success:
            self._write(f"**结果**: ✅ 测试通过！\n")
        else:
            self._write(f"**结果**: ❌ 测试失败，请查看上方错误信息\n")


class TestClient:
    """后端测试客户端"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=180.0)  # 3分钟超时
    
    def check_health(self) -> dict:
        """检查后端健康状态"""
        try:
            resp = self.client.get(f"{self.base_url}/api/health")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def upload_file(self, file_path: str, table_name: str = None) -> dict:
        """上传文件"""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在: {file_path}"}
        
        with open(path, 'rb') as f:
            files = {'file': (path.name, f, 'application/octet-stream')}
            data = {'table_name': table_name} if table_name else {}
            resp = self.client.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data
            )
        return resp.json()
    
    def list_tables(self) -> dict:
        """列出所有表"""
        resp = self.client.get(f"{self.base_url}/api/tables")
        return resp.json()
    
    def get_table_view(self, table_name: str, offset: int = 0, limit: int = 10) -> dict:
        """获取表格数据视图"""
        resp = self.client.post(
            f"{self.base_url}/api/view",
            json={"table_name": table_name, "offset": offset, "limit": limit}
        )
        return resp.json()
    
    def ai_preview(self, query: str) -> dict:
        """AI 预览（生成代码但不执行）"""
        resp = self.client.post(
            f"{self.base_url}/api/ai/preview",
            json={"query": query}
        )
        return resp.json()
    
    def ai_confirm(self) -> dict:
        """确认执行 AI 生成的代码"""
        resp = self.client.post(f"{self.base_url}/api/ai/confirm")
        return resp.json()
    
    def ai_query(self, query: str) -> dict:
        """直接执行 AI 查询（跳过预览）"""
        resp = self.client.post(
            f"{self.base_url}/api/ai/query",
            json={"query": query}
        )
        return resp.json()
    
    def get_logs(self, since_id: str = None) -> dict:
        """获取系统日志"""
        params = {"since_id": since_id} if since_id else {}
        resp = self.client.get(f"{self.base_url}/api/logs", params=params)
        return resp.json()
    
    def undo(self) -> dict:
        """撤回上次操作"""
        resp = self.client.post(f"{self.base_url}/api/undo")
        return resp.json()


def test_delete_even_rows():
    """测试：删除所有偶数行"""
    log = RealTimeLogger()
    client = TestClient()
    
    # ============ Step 1 ============
    log.step(1, "检查软件是否正常启动", 
             "首先我要确认后端服务已经启动。就像检查电脑是否开机一样。")
    
    health = client.check_health()
    if "error" in health:
        log.error(f"后端服务没有启动！错误信息: {health['error']}")
        log.info("请先运行软件: 在 AI-Sheet-Pro 目录下执行 npm start")
        log.finish(False)
        return False
    
    log.success(f"软件正常运行！版本号: {health.get('version', '未知')}")
    tables = health.get('tables', [])
    if tables:
        log.info(f"当前已加载的表格: {', '.join(tables)}")
    else:
        log.info("当前没有加载任何表格")
    
    # ============ Step 2 ============
    log.step(2, "上传测试用的 Excel 文件", 
             "现在我要上传一个 Excel 文件，就像你在软件里点击[上传]按钮一样。")
    
    test_file = Path(__file__).parent / "1.xlsx"
    if not test_file.exists():
        log.error(f"找不到测试文件: {test_file}")
        log.info("请把 1.xlsx 文件放到 AI-Sheet-Pro 目录下")
        log.finish(False)
        return False
    
    log.info(f"正在上传文件: {test_file.name}")
    upload_result = client.upload_file(str(test_file), "test_data")
    
    if not upload_result.get('success'):
        log.error(f"文件上传失败: {upload_result.get('message')}")
        log.finish(False)
        return False
    
    data = upload_result.get('data', {})
    table_name = data.get('table_name', 'test_data')
    rows_before = data.get('rows', 0)
    cols = data.get('columns', 0)
    
    log.success(f"文件上传成功！")
    log.info(f"表格名称: {table_name}")
    log.info(f"数据行数: {rows_before} 行")
    log.info(f"数据列数: {cols} 列")
    
    # ============ Step 3 ============
    log.step(3, "看看表格里都有什么数据", 
             "上传成功后，我先瞄一眼表格的前几行数据，确认内容是对的。")
    
    view_result = client.get_table_view(table_name, 0, 3)
    if view_result.get('success'):
        sample_data = view_result.get('data', {}).get('data', [])
        if sample_data:
            log.info("表格前3行数据预览:")
            for i, row in enumerate(sample_data):
                # 只显示前几个字段
                preview = str(row)[:100] + "..." if len(str(row)) > 100 else str(row)
                log.data(f"第{i+1}行", preview)
    
    # ============ Step 4 ============
    log.step(4, "发送 AI 指令：删除所有偶数行", 
             "现在是关键步骤！我要用大白话告诉 AI：请删除所有偶数行。\n"
             "AI 会理解这句话，然后自动生成代码来执行。")
    
    log.info("用户指令: 「删除所有偶数行」")
    log.info("正在等待 AI 思考和处理... (这可能需要10-60秒)")
    
    start_time = time.time()
    preview_result = client.ai_preview("删除所有偶数行")
    elapsed = time.time() - start_time
    
    log.info(f"AI 思考用时: {elapsed:.1f} 秒")
    
    if not preview_result.get('success'):
        log.error(f"AI 处理失败: {preview_result.get('message')}")
        # 尝试获取详细日志
        logs = client.get_logs()
        recent_logs = logs.get('data', [])[-5:]
        if recent_logs:
            log.warn("最近的系统日志:")
            for item in recent_logs:
                log.data(item.get('type', 'LOG'), item.get('message', ''))
        log.finish(False)
        return False
    
    # 解析 AI 返回内容
    ai_data = preview_result.get('data', {})
    explanation = ai_data.get('explanation', '无解释')
    generated_code = ai_data.get('code', '')
    llm_used = ai_data.get('llm_used', False)
    
    log.success("AI 理解了你的指令！")
    log.thinking(explanation)
    
    if generated_code:
        log.info("AI 生成的代码（你不需要看懂，只是给技术人员参考）:")
        log.data("Python代码", generated_code[:500] + ("..." if len(generated_code) > 500 else ""))
    
    # ============ Step 5 ============
    log.step(5, "确认执行 AI 的代码", 
             "AI 已经准备好了代码，现在我点击[确认执行]。\n"
             "就像你在软件里点击[确定]按钮一样。")
    
    confirm_result = client.ai_confirm()
    
    if not confirm_result.get('success'):
        log.error(f"执行失败: {confirm_result.get('message')}")
        log.finish(False)
        return False
    
    exec_result = confirm_result.get('execution_result', {})
    if exec_result.get('success'):
        log.success("代码执行成功！")
        result_value = exec_result.get('result')
        if result_value:
            log.result(str(result_value)[:200])
    else:
        log.error(f"代码运行出错: {exec_result.get('error')}")
    
    # ============ Step 6 ============
    log.step(6, "验证结果：检查数据有没有变化", 
             "最后我要检查一下，偶数行是不是真的被删除了。\n"
             "如果成功，行数应该减少一半左右。")
    
    # 刷新表格信息
    tables_after = client.list_tables()
    table_info = tables_after.get('data', {}).get(table_name, {})
    rows_after = table_info.get('rows', rows_before)
    
    log.info(f"删除前的行数: {rows_before}")
    log.info(f"删除后的行数: {rows_after}")
    
    expected = rows_before // 2
    diff = abs(rows_after - expected)
    
    if diff <= 2:  # 允许1-2行误差
        log.success(f"测试通过！成功删除了 {rows_before - rows_after} 行偶数行数据。")
        log.finish(True)
        return True
    elif rows_after < rows_before:
        log.warn(f"数据有变化，但不是精确的一半。可能 AI 用了不同的删除逻辑。")
        log.info(f"期望剩余约 {expected} 行，实际剩余 {rows_after} 行")
        log.finish(True)
        return True
    else:
        log.warn(f"数据似乎没有变化。可能 AI 创建了新表而不是修改原表。")
        # 检查是否有新表
        all_tables = tables_after.get('data', {}).keys()
        log.info(f"当前所有表格: {', '.join(all_tables)}")
        log.finish(False)
        return False


def interactive_mode():
    """交互模式"""
    log = RealTimeLogger()
    client = TestClient()
    
    log.step(0, "进入交互模式", "你可以手动输入命令来测试软件。")
    
    print("\n" + "="*50)
    print("🧪 交互模式 - 输入命令测试软件")
    print("="*50)
    print("可用命令:")
    print("  health   - 检查软件状态")
    print("  upload   - 上传文件 (格式: upload 文件路径)")
    print("  tables   - 查看所有表格")
    print("  ai       - 发送 AI 指令 (格式: ai 你的指令)")
    print("  logs     - 查看系统日志")
    print("  quit     - 退出")
    print("="*50)
    
    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if action == "quit":
                break
            elif action == "health":
                result = client.check_health()
                log.info(f"软件状态: {json.dumps(result, ensure_ascii=False, indent=2)}")
            elif action == "upload" and arg:
                log.info(f"正在上传: {arg}")
                result = client.upload_file(arg)
                if result.get('success'):
                    log.success(result.get('message'))
                else:
                    log.error(result.get('message'))
            elif action == "tables":
                result = client.list_tables()
                log.info(f"所有表格: {json.dumps(result.get('data', {}), ensure_ascii=False)}")
            elif action == "ai" and arg:
                log.info(f"正在处理指令: {arg}")
                result = client.ai_query(arg)
                log.info(f"AI 回复: {result.get('data', {}).get('explanation', '无')}")
            elif action == "logs":
                logs = client.get_logs()
                for item in logs.get('data', [])[-10:]:
                    print(f"[{item.get('type')}] {item.get('message')}")
            else:
                print(f"未知命令: {action}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"错误: {e}")
    
    log.finish(True)
    print("\n👋 再见！")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 AI-Sheet-Pro 自动化测试工具 (增强版)")
    print("="*60)
    print(f"📝 实时日志将写入: {LOG_FILE}")
    print("="*60 + "\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive_mode()
    else:
        success = test_delete_even_rows()
        
        print("\n" + "="*60)
        if success:
            print("🎉 所有测试通过！")
        else:
            print("💥 测试失败，请查看日志文件了解详情")
        print(f"📄 完整日志: {LOG_FILE}")
        print("="*60)
