"""UI样式 - 暗黑科技风"""

def load_styles():
    import streamlit as st
    st.markdown("""
    <style>
    :root {
        --bg-base: #0D0D0F;
        --bg-surface: #131316;
        --bg-elevated: #1A1A1F;
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-default: rgba(255, 255, 255, 0.1);
        --text-primary: #F4F4F5;
        --text-secondary: #A1A1AA;
        --text-tertiary: #71717A;
        --accent-blue: #63B3ED;
        --accent-glow: rgba(99, 179, 237, 0.15);
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    /* 基础 */
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    .stApp {background: var(--bg-base); font-family: 'Inter', -apple-system, sans-serif; color: var(--text-primary);}

    /* 首页居中 */
    .home-center {max-width: 100%; margin: 0 auto; padding: 25vh 24px 0; text-align: center;}
    .home-center > div {display: flex; flex-direction: column; align-items: center; width: 100%;}
    .home-center p {text-align: center !important; width: 100%;}
    .home-title {font-size: 28px; font-weight: 600; letter-spacing: 0.3em; color: var(--text-primary); margin-bottom: 48px; text-align: center;}
    .home-hint {font-size: 12px; color: var(--text-tertiary); margin-bottom: 32px; font-family: monospace; text-align: center;}

    /* 输入框 */
    [data-testid="stTextInput"] {text-align: center;}
    [data-testid="stTextInput"] > div {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-md) !important;
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    [data-testid="stTextInput"] input {
        background: transparent !important;
        color: #F4F4F5 !important;
        font-size: 17px !important;
        text-align: center !important;
    }
    [data-testid="stTextInput"] input::placeholder {color: #71717A !important;}

    /* 按钮 */
    .stButton {text-align: center;}
    .stButton > button {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.2s ease !important;
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    .stButton > button:hover {
        background: #1F1F26 !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-1px) !important;
    }

    /* 分析页 */
    .analysis-view {max-width: 900px; margin: 0 auto; padding: 40px 24px;}

    /* 卡片 */
    .hero-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg);
        padding: 48px; text-align: center; margin-bottom: 24px;
    }
    .hero-label {font-size: 11px; color: var(--accent-blue); letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 16px;}
    .hero-hex {font-size: 72px; margin-bottom: 16px;}
    .hero-name {font-size: 32px; font-weight: 700; margin-bottom: 12px;}
    .hero-quote {font-size: 15px; color: var(--text-secondary); font-style: italic;}

    /* 状态行 */
    .status-row {display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px;}
    .status-card {
        background: var(--bg-surface); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md); padding: 20px; text-align: center;
        transition: all 0.2s ease;
    }
    .status-card:hover {border-color: var(--border-default); transform: translateY(-2px);}
    .status-label {font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;}
    .status-value {font-size: 18px; font-weight: 600; font-family: monospace;}
    .status-value.danger {color: #F87171;}
    .status-value.warning {color: #FBBF24;}
    .status-value.success {color: #34D399;}

    /* 卦象卡 */
    .hex-card {
        background: var(--bg-elevated); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md); padding: 32px; text-align: center; margin: 16px 0;
    }
    .hex-symbol {font-size: 64px; margin-bottom: 12px;}
    .hex-name {font-size: 24px; font-weight: 600; margin-bottom: 8px;}
    .hex-meta {font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px;}
    .hex-quote {font-size: 14px; color: var(--text-secondary); font-style: italic;}

    /* Bit组 */
    .bit-row {display: flex; gap: 24px; justify-content: center; margin: 24px 0;}
    .bit-group {
        background: var(--bg-elevated); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md); padding: 16px 32px; text-align: center;
    }
    .bit-label {font-size: 10px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;}
    .bit-value {font-size: 24px; font-weight: 600; font-family: monospace;}
    .bit-value.inner {color: var(--accent-blue);}
    .bit-value.outer {color: #A78BFA;}

    /* 面板 */
    .status-panel {
        background: var(--bg-elevated); border-radius: var(--radius-md);
        padding: 24px; margin-top: 16px; border-left: 3px solid;
    }
    .status-panel.danger {border-color: #F87171;}
    .status-panel.warning {border-color: #FBBF24;}
    .status-panel.success {border-color: #34D399;}

    /* 策略卡 */
    .strategy-card {
        background: var(--bg-elevated); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md); padding: 24px; margin-top: 16px;
    }
    .strategy-label {font-size: 11px; color: #A78BFA; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px;}

    /* 来源 */
    .sources-title {font-size: 12px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.1em; margin: 32px 0 16px;}
    .source-item {
        background: var(--bg-surface); border-radius: var(--radius-md);
        padding: 16px 20px; margin-bottom: 8px; transition: all 0.2s ease;
    }
    .source-item:hover {background: var(--bg-elevated);}
    .source-meta {font-size: 12px; color: var(--accent-blue); margin-bottom: 4px;}
    .source-text {font-size: 13px; color: var(--text-tertiary); line-height: 1.5;}

    /* Expander */
    [data-testid="stExpander"] {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 12px;
    }
    [data-testid="stExpander"] .streamlit-expanderHeader {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderContent"] {
        background: transparent !important;
    }

    /* 聊天 */
    [data-testid="stChatMessageContent"] {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    [data-testid="stChatMessage"] img,
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"] > div:first-child {
        display: none !important;
    }
    [data-testid="stChatInput"] {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
    }

    /* 侧边栏 */
    [data-testid="stSidebar"] {background: var(--bg-surface) !important; border-right: 1px solid var(--border-subtle) !important;}
    [data-testid="stMetric"] {background: var(--bg-elevated) !important; border-radius: var(--radius-md) !important; padding: 16px !important;}
    [data-testid="stMetricValue"] {color: var(--accent-blue) !important; font-family: monospace !important;}

    /* 滚动条 */
    ::-webkit-scrollbar {width: 6px;}
    ::-webkit-scrollbar-track {background: var(--bg-base);}
    ::-webkit-scrollbar-thumb {background: var(--bg-elevated); border-radius: 3px;}
    ::selection {background: var(--accent-glow);}

    /* 隐藏 datalist 下拉 */
    datalist {display: none !important;}
    input[list] {animation: removeList 0.1s forwards;}
    @keyframes removeList {to {list-style: none;}}
    </style>
    """, unsafe_allow_html=True)
