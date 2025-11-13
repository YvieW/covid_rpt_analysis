# scripts/app.py
# ============================================================
# 📊 广东省上市公司关联交易可视化仪表盘（Dash）
# 页面结构：
#   - /           → Abstract 总览页（综合布局，自适应屏幕）
#   - /overview   → 总体趋势
#   - /region     → 地区流向
#   - /industry   → 行业分析
#   - /network    → 公司网络
# ============================================================

import os
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# 导入自定义组件
from components.overview import create_overview_layout
from components.region_flow import create_region_flow_layout
from components.industry_view import create_industry_view_layout
from components.company_network import create_company_network_layout

# ============================================================
# 🧩 数据加载
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")

df = pd.read_csv(DATA_PATH)
print(f"✅ 数据加载完成，共 {len(df):,} 条记录")

# ============================================================
# 🖥️ 初始化 Dash 应用
# ============================================================
app = Dash(
    __name__,
    use_pages=False,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "广东省上市公司关联交易可视化仪表盘"
server = app.server

# ============================================================
# 🎨 顶部导航栏
# ============================================================
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("📊 广东省上市公司关联交易分析仪表盘", className="fw-bold text-white"),
            dbc.Nav(
                [
                    dbc.NavLink("🏠 总览 (Abstract)", href="/", active="exact"),
                    dbc.NavLink("📈 总体趋势", href="/overview", active="exact"),
                    dbc.NavLink("🌏 地区流向", href="/region", active="exact"),
                    dbc.NavLink("🏭 行业分析", href="/industry", active="exact"),
                    dbc.NavLink("🏢 公司网络", href="/network", active="exact"),
                ],
                pills=True,
            ),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    sticky="top",
)

# ============================================================
# 🧱 Abstract 总览页（全屏自适应布局）
# ============================================================
abstract_layout = html.Div(
    style={
        "height": "calc(100vh - 70px)",  # 减去导航栏高度
        "display": "grid",
        "gridTemplateRows": "30% 70%",   # 上下比例
        "gridTemplateColumns": "2fr 1fr",  # 左主右辅
        "gap": "0.5rem",
        "padding": "0.5rem",
        "backgroundColor": "#f8f9fa",
    },
    children=[
        # 顶部：Overview（横跨两列）
        html.Div(
            create_overview_layout(df),
            style={
                "gridColumn": "1 / span 2",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                "padding": "0.5rem",
                "overflow": "hidden",
            },
        ),

        # 左下：公司网络（占左半 70%）
        html.Div(
            create_company_network_layout(df),
            style={
                "backgroundColor": "white",
                "borderRadius": "12px",
                "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                "padding": "0.5rem",
                "overflow": "hidden",
            },
        ),

        # 右下：上下两块（地区流向 + 行业分析）
        html.Div(
            style={
                "display": "grid",
                "gridTemplateRows": "50% 50%",
                "gap": "0.5rem",
            },
            children=[
                html.Div(
                    create_region_flow_layout(df),
                    style={
                        "backgroundColor": "white",
                        "borderRadius": "12px",
                        "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        "padding": "0.5rem",
                        "overflow": "hidden",
                    },
                ),
                html.Div(
                    create_industry_view_layout(df),
                    style={
                        "backgroundColor": "white",
                        "borderRadius": "12px",
                        "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        "padding": "0.5rem",
                        "overflow": "hidden",
                    },
                ),
            ],
        ),
    ],
)

# ============================================================
# 🧱 单页布局（普通滚动视图）
# ============================================================
overview_page = dbc.Container(create_overview_layout(df), fluid=True, class_name="p-3")
region_page = dbc.Container(create_region_flow_layout(df), fluid=True, class_name="p-3")
industry_page = dbc.Container(create_industry_view_layout(df), fluid=True, class_name="p-3")
network_page = dbc.Container(create_company_network_layout(df), fluid=True, class_name="p-3")

# ============================================================
# 🧭 主体框架（带导航 + 路由）
# ============================================================
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        navbar,
        html.Div(id="page-content", style={"height": "100vh"}),
    ]
)

# ============================================================
# 🔁 页面切换回调
# ============================================================
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/overview":
        return overview_page
    elif pathname == "/region":
        return region_page
    elif pathname == "/industry":
        return industry_page
    elif pathname == "/network":
        return network_page
    else:
        return abstract_layout  # 默认首页

# ============================================================
# 🚀 启动应用
# ============================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)
