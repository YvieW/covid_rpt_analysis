# components/filters.py
# ============================================================
# 🔧 公共筛选逻辑模块（overview / region_flow / industry / network 通用）
# ============================================================

# ---------------------------
# 🗺️ 省份区域分组（父级按钮用）
# ---------------------------
province_groups = {
    "东北": ["辽宁省", "吉林省", "黑龙江省"],
    "华北": ["北京市", "天津省", "河北省", "山西省", "内蒙古自治区"],
    "华东": ["上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省"],
    "华中": ["河南省", "湖北省", "湖南省"],
    "华南": ["广东省", "广西省", "海南省", "台湾省", "香港特别行政区", "澳门特别行政区"],
    "西南": ["重庆省", "四川省", "贵州省", "云南省", "西藏省"],
    "西北": ["陕西省", "甘肃省", "青海省", "宁夏省", "新疆省"],
}

# ---------------------------
# 📅 年份父级分组（pre / during / post）
# ---------------------------
year_groups = {
    "pre":  [2017, 2018, 2019],
    "during": [2020, 2021, 2022],
    "post": [2023, 2024],
}

# ---------------------------
# 🧩 年份 selector options（UI 直接引用）
# ---------------------------
year_options = [
    {"label": "Pre-COVID (2017-2019)", "value": "pre", "disabled": True},
    {"label": "2017", "value": 2017},
    {"label": "2018", "value": 2018},
    {"label": "2019", "value": 2019},

    {"label": "During-COVID (2020-2022)", "value": "during", "disabled": True},
    {"label": "2020", "value": 2020},
    {"label": "2021", "value": 2021},
    {"label": "2022", "value": 2022},

    {"label": "Post-COVID (2023-2024)", "value": "post", "disabled": True},
    {"label": "2023", "value": 2023},
    {"label": "2024", "value": 2024},
]


# ============================================================
# 🧰 统一过滤函数：overview / region_flow / industry / network 共用
# ============================================================
def apply_filters(df, years=None, provinces=None):
    """
    通用筛选函数（强烈推荐所有页面共用）：
      - years: 年份列表 或 None
      - provinces: 省份列表 或 None
      - 自动进行关联交易双向过滤（prvn_01 & prvn_02）

    Example:
        filtered_df = apply_filters(df, years=[2021,2022], provinces=["广东省","浙江省"])
    """

    dff = df.copy()

    # ===== 年份过滤 =====
    if years:
        dff = dff[dff["year"].isin(years)]

    # ===== 省份过滤：双向匹配关联交易双方 =====
    if provinces:
        dff = dff[
            (dff["prvn_01"].isin(provinces)) |
            (dff["prvn_02"].isin(provinces))
        ]

    return dff
