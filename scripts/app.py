# scripts/app.py
# ============================================================
# COVID-19 RPT Analysis 综合可视化仪表盘（含 Abstract 页面）
# ============================================================

import os
import pandas as pd
from dash import Dash, html, dcc, Input, Output

# 导入模块化组件
from components.overview import create_overview_layout
from components.region_flow import create_region_flow_layout
from components.industry_view import create_industry_view_layout
from components.company_network import create_company_network_layout

# ============================================================
# Step 1: 稳健路径 & 数据加载
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data_clean", "RPT_cleaned_guangdong.csv")

print(f">>> 正在加载数据文件：{DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# ============================================================
# Step 2: Dash 应用初始化
# ============================================================
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "COVID-19 RPT Analysis Dashboard"

# ============================================================
# Step 3: 构建主界面（多标签页）
# ============================================================
app.layout = html.Div([
    html.H2("💼 广东省上市公司关联交易分析仪表盘", className="text-center my-4"),

    # 顶部导航 Tabs
    dcc.Tabs(id="tabs", value="tab-abstract", children=[
        dcc.Tab(label="📊 Abstract 概览页", value="tab-abstract"),
        dcc.Tab(label="📈 总体趋势", value="tab-overview"),
        dcc.Tab(label="🌏 地区流向", value="tab-region"),
        dcc.Tab(label="🏭 行业分析", value="tab-industry"),
        dcc.Tab(label="🏢 公司网络", value="tab-network"),
    ]),

    html.Div(id="tabs-content", className="p-4")
])

# ============================================================
# Step 4: Tabs 内容回调（动态切换视图）
# ============================================================
@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value")
)
def render_tab_content(tab):
    if tab == "tab-abstract":
        # 四板块综合摘要页
        return html.Div([
            html.H3("📊 综合概览页", className="text-center mb-4"),
            html.P("此页展示广东省上市公司关联交易的总体趋势、地区流向、行业特征与公司网络结构的综合概览。"),

            # 四个小卡片式视图（2×2布局）
            html.Div([
                html.Div(create_overview_layout(df), className="basis-1/2 p-3 border rounded-lg shadow-sm"),
                html.Div(create_region_flow_layout(df), className="basis-1/2 p-3 border rounded-lg shadow-sm"),
            ], className="flex flex-wrap justify-around"),

            html.Div([
                html.Div(create_industry_view_layout(df), className="basis-1/2 p-3 border rounded-lg shadow-sm"),
                html.Div(create_company_network_layout(df), className="basis-1/2 p-3 border rounded-lg shadow-sm"),
            ], className="flex flex-wrap justify-around"),
        ], className="container mx-auto")

    elif tab == "tab-overview":
        return create_overview_layout(df)
    elif tab == "tab-region":
        return create_region_flow_layout(df)
    elif tab == "tab-industry":
        return create_industry_view_layout(df)
    elif tab == "tab-network":
        return create_company_network_layout(df)
    else:
        return html.Div("❗ 未定义的选项卡")

# ============================================================
# Step 5: 启动应用
# ============================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)
