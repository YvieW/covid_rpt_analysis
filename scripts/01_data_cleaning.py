#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
------------------------------------------------------------
Script: 01_data_cleaning.py
Project: COVID-19 RPT Analysis
Author: [Yue]
Date: 2025-11-09
Description:
    清洗并整合 RPT_Repaco, RPT_Operation, RPT_Transfer, 公司基本信息
    生成统一分析数据集 RPT_Master_Cleaned.csv
    优化：
        - 仅保留2017年及以后数据
        - 挑选分析所需核心列
        - 统一ID为字符串，减少merge内存消耗
------------------------------------------------------------
"""

import pandas as pd
import os

# ============================================================
# Step 0: 基本设置
# ============================================================
DATA_RAW_PATH = "./data_raw"
DATA_CLEAN_PATH = "./data_clean"
os.makedirs(DATA_CLEAN_PATH, exist_ok=True)

# ============================================================
# Step 1: 导入数据
# ============================================================
print(">>> Step 1: 读取原始数据文件...")

repaco = pd.read_stata(os.path.join(DATA_RAW_PATH, "RPT_Repaco.dta"))
operation = pd.read_stata(os.path.join(DATA_RAW_PATH, "RPT_Operation.dta"))
transfer = pd.read_excel(os.path.join(DATA_RAW_PATH, "RPT_Transfer.xlsx"))
firm = pd.read_excel(os.path.join(DATA_RAW_PATH, "公司基本信息.xlsx"))

print(f"读取完成：Repaco={repaco.shape}, Operation={operation.shape}, Transfer={transfer.shape}, Firm={firm.shape}")

# ============================================================
# Step 2: 标准化字段名
# ============================================================
print(">>> Step 2: 标准化字段名...")
for df in [repaco, operation, transfer, firm]:  # 加入 firm
    df.columns = df.columns.str.strip().str.lower()

# ============================================================
# Step 3: 格式化日期字段
# ============================================================
print(">>> Step 3: 格式化日期字段...")
for df in [repaco, operation, transfer]:
    if "reptdt" in df.columns:
        df["reptdt"] = pd.to_datetime(df["reptdt"], errors="coerce")
    if "annodt" in df.columns:
        df["annodt"] = pd.to_datetime(df["annodt"], errors="coerce")

# ============================================================
# Step 3.1: 年份筛选（仅保留2017年及以后数据） + 仅保留所需列 + 主板筛选
# ============================================================
print(">>> Step 3.1: 筛选2017年及以后数据，并保留分析列，并仅保留主板公司...")

def filter_after_2017(df, date_col="reptdt"):
    if date_col in df.columns:
        before = len(df)
        df = df[df[date_col] >= pd.Timestamp("2017-01-01")]
        print(f"已筛选 {date_col} ≥ 2017 的记录：{before} → {len(df)}")
    return df

# 挑选关键列
operation_cols = ["stkcd", "reptdt", "ralatedpartyid", "repart", "relation",
                  "trasub", "direction", "repat", "isam", "principl"]
repaco_cols = ["stkcd", "ralatedpartyid", "rigicy", "cogicy"]
transfer_cols = ["stkcd", "ralatedpartyid", "reptdt", "number"]
firm_cols = ["scode", "prvn", "indusb", "listplte"]

# 年份筛选 + 仅保留关键列
operation = filter_after_2017(operation, "reptdt")[operation_cols]
repaco = filter_after_2017(repaco, "reptdt")[repaco_cols]
transfer = filter_after_2017(transfer, "reptdt")[transfer_cols]
firm = firm[firm_cols]

# ============================================================
# 筛选仅“主板”公司
# ============================================================
firm = firm[firm["listplte"] == "主板"]
mainboard_stkcds = set(firm["scode"])
# 同步筛选其他表仅保留主板公司
operation = operation[operation["stkcd"].isin(mainboard_stkcds)]
repaco = repaco[repaco["stkcd"].isin(mainboard_stkcds)]
transfer = transfer[transfer["stkcd"].isin(mainboard_stkcds)]

print(f"主板公司数量：{len(mainboard_stkcds)}")
print(f"筛选后 Operation={operation.shape}, Repaco={repaco.shape}, Transfer={transfer.shape}, Firm={firm.shape}")

# ============================================================
# Step 4: 核心清洗（以 operation 为主表） + 去重
# ============================================================
print(">>> Step 4: 清洗 operation 数据，并处理重复行...")
operation_clean = operation.copy()

# 去除缺失 stkcd 或金额异常
operation_clean = operation_clean[~operation_clean["stkcd"].isna()]
operation_clean = operation_clean[operation_clean["isam"].fillna(0) > 0]

# 去重：同一 stkcd+repart+reptdt+cogicy 组合，仅保留一条
# 注意 cogicy 在 Repaco，需要先 merge 或用 placeholder
# 这里先用 merge 后的 cogicy 去重，在 merge Repaco 前可先用 placeholder 处理
operation_clean["cogicy_placeholder"] = 0  # 临时列，实际 merge 后会覆盖
operation_clean = operation_clean.drop_duplicates(subset=["stkcd", "repart", "reptdt", "cogicy_placeholder"])
operation_clean = operation_clean.drop(columns=["cogicy_placeholder"])

print(f"去重后 operation_clean 剩余记录数：{len(operation_clean)}")

# ============================================================
# Step 5: 合并 Repaco 关联方信息，并处理重复行 + 删除 rigicy/cogicy 空值
# ============================================================
print(">>> Step 5: 合并 Repaco 关联方信息，并处理重复行...")
# 统一 ID 类型为字符串
operation_clean["ralatedpartyid"] = operation_clean["ralatedpartyid"].fillna(-1).astype(str)
repaco["ralatedpartyid"] = repaco["ralatedpartyid"].fillna(-1).astype(str)
# merge
merged1 = pd.merge(operation_clean, repaco, on=["stkcd", "ralatedpartyid"], how="left")
# 删除 rigicy 或 cogicy 为空的行
merged1 = merged1.dropna(subset=["rigicy", "cogicy"])
# 再去重：同一 stkcd + repart + reptdt + cogicy
merged1 = merged1.drop_duplicates(subset=["stkcd", "repart", "reptdt", "cogicy"])

print(f"去除空 rigicy/cogicy 后，去重 merged1 记录数：{len(merged1)}")

# ============================================================
# Step 6: 合并资金往来余额（Transfer）
# ============================================================
print(">>> Step 6: 合并 Transfer 数据...")
transfer["ralatedpartyid"] = transfer["ralatedpartyid"].fillna(-1).astype(str)

# 按年份分批 merge，降低内存占用
merged_list = []
for y in merged1["reptdt"].dt.year.unique():
    temp_left = merged1[merged1["reptdt"].dt.year == y]
    temp_right = transfer[transfer["reptdt"].dt.year == y]
    merged_year = pd.merge(temp_left, temp_right, on=["stkcd", "ralatedpartyid", "reptdt"], how="left")
    merged_list.append(merged_year)
merged2 = pd.concat(merged_list, ignore_index=True)
print(f"Step 6 merge 后数据维度：{merged2.shape}")

# ============================================================
# Step 7: 合并公司基本信息（Firm）
# ============================================================
print(">>> Step 7: 合并公司基本信息...")
firm = firm.rename(columns={"scode": "stkcd"})
merged3 = pd.merge(merged2, firm.rename(columns={"indusb":"indusb"}), on="stkcd", how="left")

# ============================================================
# Step 8: 生成疫情阶段变量
# ============================================================
print(">>> Step 8: 添加疫情阶段变量...")
def assign_period(date):
    if pd.isna(date):
        return None
    y = date.year
    if y <= 2019:
        return "Pre-COVID"
    elif 2020 <= y <= 2022:
        return "During-COVID"
    else:
        return "Post-COVID"

merged3["period"] = merged3["reptdt"].apply(assign_period)

# ============================================================
# Step 9: 基本质量检查
# ============================================================
print(">>> Step 9: 数据质量检查...")
print("重复值数量：", merged3.duplicated(["stkcd", "ralatedpartyid", "reptdt"]).sum())
print("金额缺失比例：", merged3["isam"].isna().mean())
print("时间范围：", merged3["reptdt"].dt.year.describe())

# ============================================================
# Step 10: 导出整合数据
# ============================================================
output_path = os.path.join(DATA_CLEAN_PATH, "RPT_Cleaned.csv")
merged3.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f">>> Step 10: 导出完成！文件保存于：{output_path}")
print("清洗后数据维度：", merged3.shape)

print("✅ 数据清洗与整合流程全部完成！")
