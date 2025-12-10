Hi, this is a student project for DSAA 5024.
You can get an overview from this link：http://8.217.223.91:8050
Part of my work involves this visual panel, and I built this related party transaction analysis dashboard from the perspective of "Guangdong Province".
The components section of scripts is the module components of the dashboard, while the analysis section deals with empirical analysis.

The project structure is as follows:
covid_rpt_analysis/
│
├── data_raw/                 # 原始数据文件（RPT_*.dta, *.xlsx）
├── data_clean/               # 清洗后的输出数据
│   │   ├──RPT_cleaned_guangdong.csv
│ 
├── scripts/                  # 正式 Python 脚本（.py 文件）
│   ├── 01_data_cleaning.py
│   ├── app.py                          # 主入口：Dash app 启动文件
│   ├── components/		# web中调用
│   │   ├──overview.py                 
│   │   ├──industry_view.py           
│   │   ├──region_flow.py              
│   │   ├──company_network.py    
│   │   ├──province_coords.py   
│ 
├── analysis/                  #数据实证分析
│   ├── 0_data_prep.py	# 0 读取并展示数据结构
│   ├── 1_descriptives.py	# 1 描述性统计
│   ├── 2_regressions.py  # 2 基本回归（OLS + 固定效应）
│   ├── 3_robustness.py   # 3 稳健性检验（分组回归、winsorize、对数化、聚类标准误）
│   ├── 4_event_study.py  # 4 完整事件研究（Event Study）
│   ├── 5_network_analysis.py # 5 RPT 网络分析
│   ├── 6_visual_summary.py	# 6 可视化摘要：风险分担 vs 隧道
│ 
├── requirements.txt          # 环境依赖文件
├── .gitignore                # 可选：忽略缓存和数据文件
└── README.md                 # 项目简介与运行说明
