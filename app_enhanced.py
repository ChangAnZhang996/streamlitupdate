import io
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import jieba
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyecharts.options as opts
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pyecharts.charts import Bar, Funnel, HeatMap, Line, Pie, Radar, Scatter, WordCloud
from streamlit_echarts import st_pyecharts

plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

HISTORY_FILE = Path(__file__).with_name("analysis_history.json")

STOPWORDS = set([
    "的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "就", "都", "而", "及", "与", "或",
    "也", "又", "不", "没", "有", "着", "过", "啊", "呀", "哦", "呢", "吧", "吗", "这", "那",
    "此", "彼", "之", "于", "以", "为", "因", "由", "随", "和", "跟", "同", "对", "对于", "关于",
    "还", "更", "最", "很", "非常", "比较", "稍微", "一点", "一些", "全部", "所有", "每个", "各个",
    "这里", "那里", "哪里", "怎么", "怎样", "如何", "什么", "为何", "因为", "所以", "但是", "然而",
    "如果", "假如", "要是", "只要", "只有", "既然", "尽管", "虽然", "即使", "倘使", "一旦", "当",
    "则", "便", "才", "刚", "正", "将", "会", "能", "可", "可以", "要", "应", "应该", "得",
    "到", "去", "来", "上来", "下去", "进来", "出去", "起来", "过来", "过去", "嗯", "哈",
    "哼", "哎", "喂", "呃", "网址", "链接", "页面", "内容", "文章", "作者", "发布", "时间",
    "一个", "两个", "三个", "四个", "五个", "几个", "多少", "若干", "其他", "另外", "还有", "以及"
])


def apply_theme_css():
    st.markdown(
        """
        <style>
            :root {
                --primary: #5B8FF9;
                --primary-dark: #4A7ADE;
                --secondary: #61DDAA;
                --success: #52C41A;
                --warning: #FAAD14;
                --danger: #FF4D4F;
                --info: #1890FF;
                --bg-gradient-start: #f0f5ff;
                --bg-gradient-end: #e6f7ff;
                --card-bg: rgba(255, 255, 255, 0.95);
                --text-primary: #1f2937;
                --text-secondary: #6b7280;
                --text-muted: #9ca3af;
                --border-color: rgba(91, 143, 249, 0.15);
                --shadow: 0 4px 20px rgba(91, 143, 249, 0.08);
                --shadow-hover: 0 8px 30px rgba(91, 143, 249, 0.15);
            }
            html, body, [data-testid="stAppViewContainer"] {
                background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 50%, #f6ffed 100%);
                min-height: 100vh;
                color: var(--text-primary);
            }
            [data-testid="stHeader"] { 
                background: transparent !important; 
                box-shadow: none !important;
            }
            [data-testid="stToolbar"] {
                visibility: visible !important;
                display: flex !important;
            }
            [data-testid="stToolbarActions"] {
                display: none !important;
            }
            [data-testid="stToolbarActions"] * {
                display: none !important;
                visibility: hidden !important;
            }
            [data-testid="stToolbar"] button[kind="header"]:not([data-testid="stMainMenu"]):not([data-testid="stClientStatusButton"]) {
                display: none !important;
            }
            [data-testid="stMainMenu"] {
                display: none !important;
            }
            [data-testid="stClientStatusButton"] {
                display: none !important;
            }
            [data-testid="stExpandSidebarButton"] {
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: relative !important;
                z-index: 999999 !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stExpandSidebarButton"] * {
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stExpandSidebarButton"] button {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stExpandSidebarButton"] button span {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] {
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] * {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] button {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] button span {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] [data-testid*="BaseButton"] {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebarCollapseButton"] [data-testid*="BaseButton"] span {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebar"] { 
                background: #ffffff !important; 
            }
            [data-testid="stSidebarNav"] {
                background: #ffffff !important;
            }
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
            .block-container { 
                padding-top: 1.5rem; 
                padding-bottom: 2rem;
                max-width: 1200px;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .stSidebar .block-container { padding-top: 1rem; }
            .card {
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 20px;
                padding: 1.5rem;
                box-shadow: var(--shadow);
                transition: all 0.3s ease;
            }
            .card:hover {
                box-shadow: var(--shadow-hover);
                transform: translateY(-2px);
            }
            .card-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 1rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid var(--border-color);
            }
            .card-icon {
                width: 40px;
                height: 40px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
            }
            .card-title {
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }
            .badge { 
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 0.3rem 0.6rem; 
                border-radius: 999px; 
                font-size: 0.85rem; 
                font-weight: 500;
                border: 1px solid transparent;
            }
            .badge-success {
                background: rgba(82, 196, 26, 0.1);
                color: #52C41A;
                border-color: rgba(82, 196, 26, 0.2);
            }
            .badge-info {
                background: rgba(24, 144, 255, 0.1);
                color: #1890FF;
                border-color: rgba(24, 144, 255, 0.2);
            }
            .badge-warning {
                background: rgba(250, 173, 20, 0.1);
                color: #FAAD14;
                border-color: rgba(250, 173, 20, 0.2);
            }
            .stButton > button, .stDownloadButton > button {
                border-radius: 14px !important; 
                border: 0 !important; 
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                padding: 0.65rem 1.5rem !important;
                transition: all 0.2s ease !important;
                position: relative;
                overflow: hidden;
            }
            .stButton > button::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            .stButton > button:hover::before {
                left: 100%;
            }
            .btn-primary > button {
                background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important; 
                color: #fff !important; 
                box-shadow: 0 6px 20px rgba(91, 143, 249, 0.3) !important;
            }
            .btn-primary > button:hover { 
                transform: translateY(-2px); 
                box-shadow: 0 10px 28px rgba(91, 143, 249, 0.4) !important;
            }
            .btn-secondary > button {
                background: linear-gradient(135deg, #f3f4f6, #e5e7eb) !important;
                color: var(--text-primary) !important;
                box-shadow: none !important;
                border: 1px solid var(--border-color) !important;
            }
            [data-testid="stSidebar"] .stButton > button {
                background: rgba(255, 255, 255, 0.8) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
                box-shadow: none !important;
                border-radius: 10px !important;
            }
            .stTextInput > div > div > input, 
            .stSlider > div > div { 
                background: #ffffff !important; 
                color: #000000 !important; 
                border-radius: 12px !important; 
                border: 2px solid rgba(91, 143, 249, 0.15) !important;
                padding: 0.6rem 0.75rem !important;
                font-size: 0.95rem !important;
                transition: all 0.2s ease !important;
            }
            .stTextInput > div > div > input {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stTextInput"] input {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                font-weight: 500 !important;
            }
            [data-testid="stTextInput"] input[type="text"] {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                font-weight: 500 !important;
            }
            [data-testid="stTextInput"] input::placeholder {
                color: #9ca3af !important;
                -webkit-text-fill-color: #9ca3af !important;
            }

            .stTextInput > div > div > input:focus,
            .stSelectbox > div > div:focus-within,
            .stSlider > div > div:focus-within {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 3px rgba(91, 143, 249, 0.1) !important;
            }
            .stAlert { 
                border-radius: 14px !important; 
                border: none !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }
            .stSuccess { background: rgba(82, 196, 26, 0.08) !important; }
            .stWarning { background: rgba(250, 173, 20, 0.08) !important; }
            .stError { background: rgba(255, 77, 79, 0.08) !important; }
            .stInfo { background: rgba(24, 144, 255, 0.08) !important; }
            .progress-bar {
                height: 6px;
                background: rgba(91, 143, 249, 0.1);
                border-radius: 3px;
                overflow: hidden;
                margin: 0.5rem 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                border-radius: 3px;
                transition: width 0.5s ease;
            }
            .animate-fade-in {
                animation: fadeIn 0.5s ease forwards;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 1rem;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.8);
                border-radius: 14px;
                padding: 1rem;
                text-align: center;
                border: 1px solid var(--border-color);
                transition: all 0.2s ease;
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(91, 143, 249, 0.1);
            }
            .stat-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--primary);
                margin-bottom: 0.25rem;
            }
            .stat-label {
                font-size: 0.85rem;
                color: var(--text-secondary);
            }
            @media (max-width: 768px) {
                .block-container { 
                    padding-left: 0.5rem; 
                    padding-right: 0.5rem;
                    padding-top: 1rem;
                }
                .card { 
                    padding: 1rem; 
                    border-radius: 16px; 
                }
                [data-testid="stSidebar"] { 
                    width: 100vw !important; 
                    max-width: 100vw; 
                    border-right: none;
                    background: rgba(255, 255, 255, 0.95) !important;
                }
                .stTextInput > div > div > input { 
                    font-size: 1rem; 
                }
                h1 { font-size: 1.5rem !important; }
                h2 { font-size: 1.1rem !important; }
                .stats-grid { gap: 0.75rem; }
                .stat-card { padding: 0.75rem; }
                .stat-value { font-size: 1.4rem; }
            }
            .expander-header {
                font-weight: 600 !important;
                font-size: 0.95rem !important;
            }
            .dataframe-container {
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid var(--border-color);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def load_history() -> list:
    try:
        if not HISTORY_FILE.exists():
            return []
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history_list(history: list) -> None:
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def save_history(url: str, word_count: dict, top20: list, text_len: int) -> None:
    history = load_history()
    entry = {
        "timestamp": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "total_words": len(word_count),
        "text_len": text_len,
        "top20": top20,
        "summary": top20[:5] if top20 else [],
    }
    history.insert(0, entry)
    history = history[:15]
    save_history_list(history)


def fetch_web_text(url: str):
    if not url or not isinstance(url, str):
        return "", "请输入文章地址后再开始分析。"

    cleaned_url = url.strip()
    if not is_valid_url(cleaned_url):
        return "", "请输入一个有效的 http:// 或 https:// 链接。"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(cleaned_url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup(["script", "style", "noscript", "iframe", "nav", "header", "footer"]):
            tag.decompose()

        article_tag = soup.find("article") or soup.find("main")
        if article_tag:
            text = article_tag.get_text(strip=True, separator="\n")
        else:
            body = soup.body
            if body is None:
                return "", "页面结构异常，未能提取到正文内容。"
            text = body.get_text(strip=True, separator="\n")

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。！？、；：""''（）《》【】]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if not text or len(text) < 50:
            return "", "抓取到的内容过短，建议更换其他文章链接。"

        return text, None
    except requests.exceptions.Timeout:
        return "", "⏰ 访问超时，请稍后重试或换一个响应更快的页面。"
    except requests.exceptions.ConnectionError:
        return "", "🔌 网络连接失败，请检查当前网络或页面是否可访问。"
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "未知"
        return "", f"❌ 页面请求失败（HTTP {status}），请确认链接是否正确。"
    except Exception as exc:
        return "", f"⚠️ 抓取网页内容时出现异常：{exc}"


def word_segment_and_count(text: str, min_freq: int):
    words = jieba.lcut(text)
    filtered_words = [
        word for word in words
        if len(word) > 1 and word not in STOPWORDS and not re.match(r"^\d+$", word)
    ]
    word_count = Counter(filtered_words)
    word_count = {word: count for word, count in word_count.items() if count >= min_freq}
    sorted_word_count = dict(sorted(word_count.items(), key=lambda x: x[1], reverse=True))
    top20 = list(sorted_word_count.items())[:20]
    top10 = list(sorted_word_count.items())[:10]
    return sorted_word_count, top20, top10


def calculate_stats(word_count: dict, top20: list, text_length: int):
    total_words = sum(word_count.values())
    unique_words = len(word_count)
    avg_freq = total_words / unique_words if unique_words > 0 else 0
    top_word = top20[0][0] if top20 else ""
    top_freq = top20[0][1] if top20 else 0
    coverage_rate = sum(count for _, count in top20) / total_words if total_words > 0 else 0
    
    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "avg_freq": round(avg_freq, 2),
        "top_word": top_word,
        "top_freq": top_freq,
        "coverage_rate": round(coverage_rate * 100, 1),
        "text_length": text_length
    }


def create_wordcloud(word_count: dict, color_theme="default"):
    data = list(word_count.items())[:120]
    colors = ["#5B8FF9", "#61DDAA", "#F6BD16", "#E86452", "#6DC8EC", "#9270CA", "#FF9F7F"]
    
    return (
        WordCloud()
        .add(series_name="词频", data_pair=data, word_size_range=[12, 120], shape="circle")
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="文章词汇词云图", 
                title_textstyle_opts=opts.TextStyleOpts(font_size=22, color="#1f2937"),
                pos_left="center"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c}"),
            visualmap_opts=opts.VisualMapOpts(
                min_=1, 
                max_=max([v for _, v in data]) if data else 1,
                range_color=colors,
                range_text=["高频", "低频"],
                is_piecewise=True
            )
        )
    )


def create_chart(chart_type: str, top20: list, stats: dict = None):
    words = [item[0] for item in top20]
    counts = [item[1] for item in top20]

    if chart_type == "柱状图":
        bar = Bar(init_opts=opts.InitOpts(width="100%", height="500px"))
        bar.add_xaxis(words)
        bar.add_yaxis("词频", counts)
        bar.reversal_axis()
        bar.set_global_opts(
            title_opts=opts.TitleOpts(title="词频前20词汇", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
            xaxis_opts=opts.AxisOpts(
                type_="value",
                name="词频",
                name_textstyle_opts=opts.TextStyleOpts(color="#6b7280"),
                axislabel_opts=opts.LabelOpts(color="#374151")
            ),
            yaxis_opts=opts.AxisOpts(
                type_="category",
                name="词汇",
                name_textstyle_opts=opts.TextStyleOpts(color="#6b7280"),
                axislabel_opts=opts.LabelOpts(color="#374151")
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow")
        )
        bar.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color="#5B8FF9")
        )
        return bar

    if chart_type == "折线图":
        line = Line(init_opts=opts.InitOpts(width="100%", height="500px"))
        line.add_xaxis(words)
        line.add_yaxis("词频", counts)
        line.set_global_opts(
            title_opts=opts.TitleOpts(title="词频趋势分析", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(rotate=-30, color="#374151")
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                name="词频",
                name_textstyle_opts=opts.TextStyleOpts(color="#6b7280"),
                axislabel_opts=opts.LabelOpts(color="#374151")
            )
        )
        line.set_series_opts(
            linestyle_opts=opts.LineStyleOpts(width=3),
            itemstyle_opts=opts.ItemStyleOpts(color="#5B8FF9"),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(type_="max", name="最高"), opts.MarkPointItem(type_="min", name="最低")]
            ),
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average", name="平均值")])
        )
        return line

    if chart_type == "饼图":
        pie = Pie(init_opts=opts.InitOpts(width="100%", height="500px"))
        pie.add("", list(zip(words, counts)), radius=["40%", "70%"])
        pie.set_global_opts(
            title_opts=opts.TitleOpts(title="词频分布占比", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="75%", textstyle_opts=opts.TextStyleOpts(color="#6b7280"))
        )
        pie.set_series_opts(
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c} ({d}%)"),
            label_opts=opts.LabelOpts(formatter="{b}: {d}%")
        )
        return pie

    if chart_type == "雷达图":
        radar_words = words[:8]
        radar_counts = counts[:8]
        if not radar_words:
            return None
        max_val = max(radar_counts) if max(radar_counts) > 0 else 1
        schema = [opts.RadarIndicatorItem(name=word, max_=max_val) for word in radar_words]
        radar = Radar(init_opts=opts.InitOpts(width="100%", height="450px"))
        radar.add_schema(schema=schema, splitarea_opt=opts.SplitAreaOpts(is_show=True))
        radar.add("词频", [radar_counts], 
            linestyle_opts=opts.LineStyleOpts(width=2, color="#5B8FF9"),
            areastyle_opts=opts.AreaStyleOpts(color="rgba(91, 143, 249, 0.1)"))
        radar.set_global_opts(
            title_opts=opts.TitleOpts(title="词频对比分析", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
            legend_opts=opts.LegendOpts(selected_mode="single")
        )
        return radar

    if chart_type == "散点图":
        scatter = Scatter(init_opts=opts.InitOpts(width="100%", height="500px"))
        scatter.add_xaxis(words)
        scatter.add_yaxis("词频", counts, symbol_size=20)
        scatter.set_global_opts(
            title_opts=opts.TitleOpts(title="词频散点分布", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(rotate=-30, color="#374151")
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                name="词频",
                name_textstyle_opts=opts.TextStyleOpts(color="#6b7280"),
                axislabel_opts=opts.LabelOpts(color="#374151")
            )
        )
        scatter.set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color="#5B8FF9")
        )
        return scatter
    if chart_type == "热力图":
        wx = words[:10]
        wy = words[:10]
        vc = counts[:10]
        if not wx or not vc:
            return None
        heat_data = [[i, j, vc[j]] for i in range(len(wx)) for j in range(len(wy))]
        return (
            HeatMap(init_opts=opts.InitOpts(width="100%", height="500px"))
            .add_xaxis(wx)
            .add_yaxis("词汇", wy, heat_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词汇关联热力图", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
                visualmap_opts=opts.VisualMapOpts(min_=min(vc), max_=max(vc), is_piecewise=True),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45, color="#6b7280")),
                yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#6b7280"))
            )
        )
    if chart_type == "漏斗图":
        return (
            Funnel(init_opts=opts.InitOpts(width="100%", height="500px"))
            .add("词频", list(zip(words, counts)), sort_="descending")
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频层级分布", title_textstyle_opts=opts.TextStyleOpts(font_size=18, color="#1f2937")),
                tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="80%", textstyle_opts=opts.TextStyleOpts(color="#6b7280"))
            )
        )
    return None


def export_to_excel(word_count: dict, top20: list, stats: dict):
    full_df = pd.DataFrame(sorted(word_count.items(), key=lambda x: x[1], reverse=True), columns=["词汇", "词频"])
    top_df = pd.DataFrame(top20, columns=["词汇", "词频"])
    stats_df = pd.DataFrame([{
        "统计项": ["总词数", "唯一词汇数", "平均词频", "最高频词", "最高词频", "TOP20覆盖率", "原文长度"],
        "数值": [
            stats["total_words"],
            stats["unique_words"],
            stats["avg_freq"],
            stats["top_word"],
            stats["top_freq"],
            f"{stats['coverage_rate']}%",
            stats["text_length"]
        ]
    }])

    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            stats_df.to_excel(writer, sheet_name="统计概览", index=False)
            top_df.to_excel(writer, sheet_name="TOP20词汇", index=False)
            full_df.to_excel(writer, sheet_name="全部词频", index=False)
        output.seek(0)
        return output
    except Exception as exc:
        st.error(f"Excel 导出失败：{exc}")
        return None


def export_to_csv(word_count: dict, top20: list):
    full_df = pd.DataFrame(sorted(word_count.items(), key=lambda x: x[1], reverse=True), columns=["词汇", "词频"])
    return full_df.to_csv(index=False, encoding="utf-8-sig")


def render_stats_cards(stats: dict):
    cols = st.columns(6)
    
    stats_items = [
        ("📝", "总词数", stats["total_words"]),
        ("🔤", "唯一词汇", stats["unique_words"]),
        ("📊", "平均词频", f"{stats['avg_freq']}"),
        ("🏆", "最高频词", stats["top_word"]),
        ("🔥", "最高词频", stats["top_freq"]),
        ("📈", "TOP20覆盖率", f"{stats['coverage_rate']}%")
    ]
    
    for col, (icon, label, value) in zip(cols, stats_items):
        with col:
            st.markdown(
                f'''
                <div style="background:rgba(255,255,255,0.8);border-radius:14px;padding:1rem;text-align:center;border:1px solid rgba(91,143,249,0.15);">
                    <div style="font-size:1.5rem;margin-bottom:0.3rem;">{icon}</div>
                    <div style="font-size:1.6rem;font-weight:700;color:#5B8FF9;margin-bottom:0.25rem;">{value}</div>
                    <div style="font-size:0.85rem;color:#6b7280;">{label}</div>
                </div>
                ''',
                unsafe_allow_html=True
            )


def render_analysis_result(result: dict, chart_type: str):
    text = result["text"]
    word_count = result["word_count"]
    top20 = result["top20"]
    stats = result["stats"]

    # st.markdown('<div class="card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("📊 统计概览", divider="blue")
    render_stats_cards(stats)
    with st.expander("📄 查看抓取到的文本", expanded=False):
        st.text_area("抓取内容预览", value=text, height=200)
    st.markdown('</div>', unsafe_allow_html=True)

    # st.markdown('<div class="card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("🏆 词频排名前20", divider="blue")
    top20_df = pd.DataFrame(top20, columns=["词汇", "词频"])
    st.dataframe(top20_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # st.markdown('<div class="card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("☁️ 词汇词云图", divider="blue")
    st_pyecharts(create_wordcloud(word_count), width="100%", height="500px")
    st.markdown('</div>', unsafe_allow_html=True)

    # st.markdown('<div class="card animate-fade-in">', unsafe_allow_html=True)
    st.subheader(f"📈 {chart_type}", divider="blue")
    chart = create_chart(chart_type, top20, stats)
    if chart:
        st_pyecharts(chart, width="100%", height="500px")
    else:
        st.warning("当前图表类型暂不可用，请切换其他类型。")
    st.markdown('</div>', unsafe_allow_html=True)

    # st.markdown('<div class="card animate-fade-in">', unsafe_allow_html=True)
    st.subheader("📋 全部词频列表", divider="blue")
    with st.expander("点击展开查看完整词频列表", expanded=False):
        md = "\n".join(f"- **{w}**: {c}" for w, c in word_count.items())
        st.markdown(md)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    excel_file = export_to_excel(word_count, top20, stats)
    csv_data = export_to_csv(word_count, top20)
    
    with col1:
        if excel_file is not None:
            st.download_button(
                label="📥 导出为 Excel",
                data=excel_file.getvalue(),
                file_name=f"词频分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    
    with col2:
        st.download_button(
            label="📥 导出为 CSV",
            data=csv_data,
            file_name=f"词频分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def analyze_url(url: str, min_freq: int, chart_type: str):
    with st.status("🔄 正在处理...", expanded=True) as status:
        status.update(label="📡 正在抓取网页内容...")
        text, error = fetch_web_text(url)
        if error:
            st.warning(error)
            return None
        
        status.update(label="🔤 正在进行中文分词...")
        time.sleep(0.3)
        word_count, top20, top10 = word_segment_and_count(text, min_freq)
        if not word_count:
            st.warning("分词结果为空，请适当降低筛选阈值后重试。")
            return None
        
        status.update(label="📊 正在统计分析...")
        time.sleep(0.2)
        stats = calculate_stats(word_count, top20, len(text))
        
        status.update(label="✅ 分析完成！")
        status.update(state="complete", expanded=False)

    save_history(url, word_count, top20, len(text))
    
    result = {
        "url": url,
        "text": text,
        "word_count": word_count,
        "top20": top20,
        "stats": stats
    }
    st.session_state["last_analysis"] = result
    
    render_analysis_result(result, chart_type)
    return result


def clear_url_input():
    st.session_state["url_input"] = ""
    st.session_state["last_analysis"] = None
    st.session_state["auto_run"] = False
    


def select_history(url: str):
    st.session_state["url_input"] = url
    st.session_state["auto_run"] = True


def delete_history(index: int):
    history = load_history()
    if 0 <= index < len(history):
        history.pop(index)
        save_history_list(history)
        st.rerun()


def main():
    st.set_page_config(page_title="文章词频分析工具", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
    apply_theme_css()

    st.markdown(
        '''
        <div class="card" style="text-align:center;padding:2rem;">
            <div style="font-size:3rem;margin-bottom:0.5rem;">📊</div>
            <h1 style="margin-bottom:0.3rem; color:#1f2937; font-size:1.8rem;">文章词频分析与可视化工具</h1>
            <p style="color:#6b7280; margin-top:0.2rem; font-size:0.95rem;">
                支持网页抓取 • 智能分词 • 词频统计 • 多维度可视化 • 历史回看 • 数据导出
            </p>
            <div style="margin-top:1rem;">
                <span class="badge badge-info">Web Scraping</span>
                <span class="badge badge-success">中文分词</span>
                <span class="badge badge-warning">可视化</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.sidebar.title("🔧 分析设置")
    
    st.sidebar.subheader("📈 图表类型")
    chart_types = ["柱状图", "折线图", "饼图", "雷达图", "散点图", "热力图", "漏斗图"]
    selected_chart = st.sidebar.selectbox("选择可视化图表", chart_types, index=0, key="chart_select")
    
    st.sidebar.subheader("🎯 筛选阈值")
    min_freq = st.sidebar.slider("低频词过滤（最小词频）", min_value=1, max_value=15, value=2, step=1)
    
    st.sidebar.subheader("⚡ 显示选项")
    show_stats = st.sidebar.checkbox("显示统计概览", value=True)
    show_wordcloud = st.sidebar.checkbox("显示词云图", value=True)
    show_chart = st.sidebar.checkbox("显示图表", value=True)

    st.sidebar.divider()
    
    st.sidebar.subheader("📚 最近分析历史")
    history = load_history()
    
    if history:
        for idx, item in enumerate(history):
            with st.sidebar.expander(f"📅 {item['timestamp']}", expanded=False):
                st.markdown(f"**链接**: {item['url']}")
                st.markdown(f"**词汇数**: {item['total_words']}")
                st.markdown(f"**文本长度**: {item['text_len']}")
                
                col1, col2 = st.sidebar.columns([2, 1])
                with col1:
                    st.button("🔄 重新分析", key=f"history_{idx}", use_container_width=True,
                              on_click=select_history, args=(item["url"],))
                with col2:
                    st.button("🗑 删除", key=f"del_{idx}", use_container_width=True,
                              on_click=delete_history, args=(idx,))
    else:
        st.sidebar.info("暂无历史记录，首次分析后会自动保存。")

    st.sidebar.divider()
    st.sidebar.markdown(
        '''
        <div style="padding:1rem;background:rgba(91, 143, 249, 0.05);border-radius:12px;">
            <h4 style="margin-bottom:0.5rem;">💡 使用提示</h4>
            <ul style="margin:0;padding-left:1.2rem;font-size:0.85rem;color:#6b7280;">
                <li>输入文章URL即可开始分析</li>
                <li>调整阈值过滤低频词汇</li>
                <li>支持多种图表可视化</li>
                <li>历史记录自动保存</li>
                <li>支持导出Excel/CSV</li>
            </ul>
        </div>
        ''',
        unsafe_allow_html=True
    )

    url = st.text_input(
        "请输入文章URL", 
        key="url_input", 
        placeholder="例如：https://www.example.com/article.html",
        help="支持 HTTP 和 HTTPS 链接"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        analyze_btn = st.button("🚀 开始分析", type="primary", use_container_width=True, 
                               help="点击开始抓取并分析文章内容")
    with col2:
        clear_btn = st.button("🧹 清空", on_click=clear_url_input, use_container_width=True,
                              help="清空输入和分析结果")
    with col3:
        if st.session_state.get("last_analysis"):
            st.download_button(
                "📥 导出数据",
                data=export_to_csv(
                    st.session_state["last_analysis"]["word_count"],
                    st.session_state["last_analysis"]["top20"]
                ),
                file_name=f"词频分析_{datetime.now().strftime('%Y%m%d')}.csv",
                use_container_width=True
            )

    last_analysis = st.session_state.get("last_analysis")
    
    if last_analysis and last_analysis.get("url") == url and not analyze_btn and not st.session_state.get("auto_run"):
        render_analysis_result(last_analysis, selected_chart)
        return

    if st.session_state.get("auto_run"):
        st.session_state["auto_run"] = False
        with st.spinner("⏳ 正在加载历史记录..."):
            time.sleep(0.3)
            analyze_url(st.session_state.get("url_input", url), min_freq, selected_chart)
        return

    if analyze_btn and url:
        analyze_url(url, min_freq, selected_chart)
    elif analyze_btn and not url:
        st.warning("⚠️ 请先输入有效的文章URL")


if __name__ == "__main__":
    main()