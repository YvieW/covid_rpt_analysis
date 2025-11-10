#!/usr/bin/env python 
# -*- coding: utf-8 -*-
"""
------------------------------------------------------------
Script: 01_data_cleaning.py
Project: COVID-19 RPT Analysis
Author: Yue
Date: 2025-11-11
Description:
    清洗并整合 RPT_Repaco, RPT_Operation, 公司基本信息
    以 Operation 为主表，按 stkcd+reptdt+repart 合并 Repaco
    再按 stkcd 与 Firm 合并公司特征
    优化：
        - 仅保留2017年及以后数据
        - 仅主板公司
        - 仅关键字段
        - 筛选 repttype=1
        - 增加 Firm 字段 pftn 并重命名为 pftn_01
        - 增加 Operation 字段 repat
        - 增加 Repaco 字段 rigicy, cogicy
        - 若 pannrsm 缺失，按同公司+同年度+同 repat+同 direction 估算
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
firm = pd.read_excel(os.path.join(DATA_RAW_PATH, "公司基本信息.xlsx"))

print(f"读取完成：Repaco={repaco.shape}, Operation={operation.shape}, Firm={firm.shape}")

# ============================================================
# Step 2: 标准化字段名
# ============================================================
print(">>> Step 2: 标准化字段名...")
for df in [repaco, operation, firm]:
    df.columns = df.columns.str.strip().str.lower()

# ============================================================
# Step 3: 格式化日期字段
# ============================================================
print(">>> Step 3: 格式化日期字段...")
for df in [repaco, operation]:
    if "reptdt" in df.columns:
        df["reptdt"] = pd.to_datetime(df["reptdt"], errors="coerce")

# ============================================================
# Step 3.1: 年份筛选 + repttype=1 + 仅保留所需列 + 主板筛选
# ============================================================
print(">>> Step 3.1: 筛选 repttype=1 且 2017年及以后数据，并仅保留主板公司...")

def filter_after_2017(df, date_col="reptdt"):
    if date_col in df.columns:
        before = len(df)
        df = df[df[date_col] >= pd.Timestamp("2017-01-01")]
        print(f"已筛选 {date_col} ≥ 2017 的记录：{before} → {len(df)}")
    return df

operation_cols = ["stkcd", "reptdt", "repart", "relation",
                  "trasub", "direction", "repttype", "isam",
                  "pannrsm", "repat"] 

repaco_cols = ["stkcd", "reptdt", "repart",
               "corebs", "site"] 
firm_cols = ["scode", "prvn", "pftn", "indusb", "indcodeb",
             "coname_cn", "listplte"]

operation = filter_after_2017(operation, "reptdt")[operation_cols]
repaco = filter_after_2017(repaco, "reptdt")[repaco_cols]
firm = firm[firm_cols]

# ✅ 仅保留 repttype = 1 的 operation 数据
before_len = len(operation)
operation = operation[operation["repttype"] == 1]
print(f"筛选 repttype=1：{before_len} → {len(operation)}")

# ✅ 仅主板公司
firm_main = firm[firm["listplte"] == "主板"].copy()
mainboard_stkcds = set(firm_main["scode"])
operation = operation[operation["stkcd"].isin(mainboard_stkcds)]
repaco = repaco[repaco["stkcd"].isin(mainboard_stkcds)]

print(f"主板公司数量：{len(mainboard_stkcds)}")
print(f"筛选后 Operation={operation.shape}, Repaco={repaco.shape}, Firm={firm_main.shape}")

# ============================================================
# Step 4: 合并 Repaco（按 stkcd + reptdt + repart）
# ============================================================
print(">>> Step 4: 合并 Repaco 信息...")
merged = pd.merge(
    operation,
    repaco,
    on=["stkcd", "reptdt", "repart"],
    how="left"
)
print(f"合并后维度：{merged.shape}")

# ============================================================
# Step 4.1: 若 pannrsm 缺失，则按同公司+同年度+同 repat+同 direction 估算
# ============================================================
print(">>> Step 4.1: 估算缺失的 Pannrsm...")

# 提取年份
merged["year"] = merged["reptdt"].dt.year

# 计算每组总 isam
group_sum = (
    merged.groupby(["stkcd", "year", "repat", "direction"], dropna=False)["isam"]
    .transform("sum")
)

# 标记缺失的 pannrsm 行
missing_mask = merged["pannrsm"].isna()

# 避免除零
group_sum_safe = group_sum.replace(0, pd.NA)

# 计算估算值：单行 isam / 同组 isam 总和（比重近似）
merged.loc[missing_mask, "pannrsm"] = (
    merged.loc[missing_mask, "isam"] / group_sum_safe.loc[missing_mask]
)

print(f"已填补 Pannrsm 缺失值：{missing_mask.sum()} 行（按组估算）")

# ============================================================
# Step 5: 合并公司基本信息（Firm）
# ============================================================
print(">>> Step 5: 合并公司基本信息...")
firm_main = firm_main.rename(columns={"scode": "stkcd"})
merged = pd.merge(
    merged,
    firm_main,
    on="stkcd",
    how="left"
)
print(f"合并后维度：{merged.shape}")

# ============================================================
# Step 5.1: 重命名字段
# ============================================================
print(">>> Step 5.1: 重命名关键字段...")
rename_map = {
    "stkcd": "stkcd_01",
    "prvn": "prvn_01",
    "coname_cn": "coname_cn_01",
    "indusb": "indusb_01",
    "indcodeb": "indcodeb_01",
    "pftn": "pftn_01"
}
merged = merged.rename(columns=rename_map)
print("字段已重命名：", rename_map)

# ============================================================
# Step 5.2: 若 “repart” 能在 firm 中找到相同 “coname_cn”，则补充 prvn_02、pftn_02
# ============================================================
print(">>> Step 5.2: 匹配关联方公司信息（prvn_02, pftn_02）...")

# 准备 firm 对照表：只保留关联方所需字段
firm_match = firm_main[["coname_cn", "prvn", "pftn"]].copy()

# 合并（左连接：merged.repart ↔ firm.coname_cn）
merged = pd.merge(
    merged,
    firm_match,
    how="left",
    left_on="repart",
    right_on="coname_cn",
    suffixes=("", "_rpt")
)

# 将匹配到的列重命名为 prvn_02, pftn_02
merged = merged.rename(columns={
    "prvn": "prvn_02",
    "pftn": "pftn_02"
})

# 删除右侧多余的 coname_cn（即合并时生成的重复列）
if "coname_cn_rpt" in merged.columns:
    merged = merged.drop(columns=["coname_cn_rpt"])

# 输出匹配情况
matched_rows = merged["prvn_02"].notna().sum()
print(f"成功为 {matched_rows} 条记录匹配到关联方公司信息（prvn_02, pftn_02）。")

# ============================================================
# Step 6: 数据质量检查
# ============================================================
print(">>> Step 6: 数据质量检查...")
print("缺失比例：")
print(merged.isna().mean().round(3))
print("时间范围：")
print(merged["reptdt"].dt.year.describe())


# ============================================================
# Step 7: 添加疫情阶段变量
# ============================================================
print(">>> Step 7: 添加疫情阶段变量...")

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

merged["period"] = merged["reptdt"].apply(assign_period)

print("Period 列添加完成，分布如下：")
print(merged["period"].value_counts(dropna=False))


# ============================================================
# Step 8: 导出整合数据
# ============================================================
output_path = os.path.join(DATA_CLEAN_PATH, "RPT_cleaned.csv")
merged.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f">>> Step 8: 导出完成！文件保存于：{output_path}")
print("清洗后数据维度：", merged.shape)

print("✅ 数据清洗与整合流程全部完成！")

