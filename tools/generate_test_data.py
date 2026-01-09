import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# 确保数据目录存在
DATA_DIR = r"d:\软件集合\网页自动化\AI-Sheet-Pro\test_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def create_cleaning_data():
    """生成第一类：数据清洗测试数据"""
    print("Generating cleaning_data.csv...")
    data = {
        "User ID": range(1, 101),
        "Name": [" 张三", "李 四 ", "王五", "Zhao Liu", "Mike ", "Sarah", "Unknown", "User8", " Test ", "Alice"] * 10,
        "Phone": ["13800138000", "13912345678", "123", "abc", "13800138000", None, "15900001111", "999", "138 0000 0000", "13800138000"] * 10,
        "Date": ["2025/01/01", "2025-01-02", "01-03-2025", "2025.01.04", "Invalid", "20250106", "2025-01-07", "2025/1/8", "Jan 9, 2025", "2025-01-10"] * 10,
        "Amount": ["$100", "¥200.5", "300", "-50", "0", "1,000", "$50.00", "N/A", "Unknown", "500"] * 10,
        "Gender": ["男", "女", "M", "F", "Male", "Female", "未知", "男", "女", "M"] * 10,
        "Description": ["<p>Good</p>", "Nice\nItem", "Bad", "OK", "<h1>Title</h1>", "Line1\r\nLine2", "Normal", "<b>Bold</b>", "Test", "End"] * 10,
        "Address": ["广东省 广州市", "北京 北京市", "上海 上海市", "浙江省 杭州市", "江苏省 南京市", "四川省 成都市", "Unknown", "海外", "广东省 深圳市", "湖北省 武汉市"] * 10,
        "Score": [55, 65, 75, 40, 90, 85, 30, 95, 60, 50] * 10, # 包含不及格
        "Email": [f"user{i}@example.com" if i % 5 != 0 else "" for i in range(100)]
    }
    df = pd.DataFrame(data)
    # 插入一些重复行
    df = pd.concat([df, df.iloc[:5]], ignore_index=True)
    # 插入空列
    df["EmptyCol"] = np.nan
    df.to_csv(os.path.join(DATA_DIR, "cleaning_data.csv"), index=False, encoding='utf-8-sig')

def create_multi_table_data():
    """生成第二类：多表关联数据"""
    print("Generating multi_table files...")
    # 表1: 员工表
    emps = pd.DataFrame({
        "EmpID": range(1, 21),
        "Name": [f"Emp{i}" for i in range(1, 21)],
        "DeptID": [random.randint(1, 5) for _ in range(20)],
        "Salary": [random.randint(5000, 20000) for _ in range(20)]
    })
    emps.to_csv(os.path.join(DATA_DIR, "employees.csv"), index=False)

    # 表2: 部门表
    depts = pd.DataFrame({
        "DeptID": range(1, 6),
        "DeptName": ["HR", "Sales", "IT", "Finance", "Marketing"]
    })
    depts.to_csv(os.path.join(DATA_DIR, "departments.csv"), index=False)

    # 库存表 & 价格表
    products = ["P001", "P002", "P003", "P004", "P005"]
    stock = pd.DataFrame({"ProductModel": products, "Quantity": [100, 50, 200, 0, 80]})
    prices = pd.DataFrame({"ProductModel": products, "Price": [10.5, 20.0, 5.0, 100.0, 15.0]})
    stock.to_csv(os.path.join(DATA_DIR, "stock.csv"), index=False)
    prices.to_csv(os.path.join(DATA_DIR, "prices.csv"), index=False)
    
    # 销售表 A (上个月), B (这个月)
    sales_a = pd.DataFrame({"CustomerID": range(1, 11), "Amount": [100*i for i in range(1, 11)]})
    sales_b = pd.DataFrame({"CustomerID": range(5, 15), "Amount": [150*i for i in range(1, 11)]}) # 5-10 重叠
    sales_a.to_csv(os.path.join(DATA_DIR, "sales_last_month.csv"), index=False)
    sales_b.to_csv(os.path.join(DATA_DIR, "sales_this_month.csv"), index=False)

def create_complex_query_data():
    """生成第三、四类：筛选与统计"""
    print("Generating sales_records.csv...")
    rows = 500
    dates = [datetime(2025, 1, 1) + timedelta(days=random.randint(0, 90)) for _ in range(rows)]
    data = {
        "OrderID": range(1000, 1000 + rows),
        "Date": [d.strftime("%Y-%m-%d") for d in dates],
        "SalesPerson": [random.choice(["Zhang San", "Li Si", "Wang Wu", "Alice", "Bob"]) for _ in range(rows)],
        "Region": [random.choice(["广东", "北京", "上海", "浙江", "四川"]) for _ in range(rows)],
        "Category": [random.choice(["Electronics", "Clothing", "Home", "Books"]) for _ in range(rows)],
        "Product": [f"Prod_{i}" for i in range(rows)],
        "Quantity": [random.randint(1, 50) for _ in range(rows)],
        "UnitPrice": [random.randint(10, 500) for _ in range(rows)],
        "Discount": [random.choice([0.8, 0.9, 0.95, 1.0]) for _ in range(rows)],
        "Status": [random.choice(["Completed", "Cancelled", "Pending", "Returned"]) for _ in range(rows)],
        "CustomerName": [f"Cust_{i}" for i in range(rows)],
        "Gender": [random.choice(["Male", "Female"]) for _ in range(rows)],
        "Remark": [random.choice(["", "OK", "投诉: Quality", "退款申请", "Urgent"]) for _ in range(rows)]
    }
    df = pd.DataFrame(data)
    df["TotalAmount"] = df["Quantity"] * df["UnitPrice"] * df["Discount"]
    df.to_csv(os.path.join(DATA_DIR, "sales_records.csv"), index=False)

if __name__ == "__main__":
    create_cleaning_data()
    create_multi_table_data()
    create_complex_query_data()
    print("All test data generated in", DATA_DIR)
