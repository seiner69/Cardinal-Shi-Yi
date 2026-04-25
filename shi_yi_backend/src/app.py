"""
史易枢机 - 6-Bit FSM 分析引擎
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.llm.chain import IChingChain
from src.db.faiss_client import FAISSIChingClient
from src.ui import load_styles, render_fsm_section, render_retrieval_results, render_loading


@st.cache_resource
def get_chain(): return IChingChain()

@st.cache_resource
def get_db_client():
    client = FAISSIChingClient()
    client.connect()
    return client


def main():
    st.set_page_config(page_title="史易枢机", page_icon="☯", layout="wide", initial_sidebar_state="collapsed")
    load_styles()

    if 'chain' not in st.session_state: st.session_state.chain = get_chain()
    if 'messages' not in st.session_state: st.session_state.messages = []
    if 'view' not in st.session_state: st.session_state.view = 'home'
    if 'processing' not in st.session_state: st.session_state.processing = False

    # 首页
    if st.session_state.view == 'home':
        st.markdown('<div class="home-center">', unsafe_allow_html=True)
        st.markdown('<div class="home-title">史易枢机</div>', unsafe_allow_html=True)
        st.markdown('<div class="home-hint">Enter 提交</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            query = st.text_input("", placeholder="输入历史事件 | 推演宇宙拓扑", label_visibility="collapsed", key="home_input")
            submitted = st.button("推演", use_container_width=True)

        if submitted and query:
            st.session_state.view = 'analysis'
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.processing = True
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="position:fixed;bottom:40px;width:100%;text-align:center;font-size:11px;color:var(--text-tertiary);">6-BIT FSM TOPOLOGY ENGINE</div>', unsafe_allow_html=True)

    # 分析页
    else:
        # 首次处理
        if st.session_state.processing and len(st.session_state.messages) == 1:
            st.session_state.processing = False
            with st.chat_message("assistant"):
                render_loading()
                try:
                    chain = get_chain()
                    prompt = st.session_state.messages[0]["content"]
                    fsm_result, retrieval = chain.run(prompt)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "retrieval_results": retrieval,
                        "fsm_analysis": {
                            "inner_system": fsm_result.inner_system,
                            "outer_system": fsm_result.outer_system,
                            "inner_bits": fsm_result.inner_bits,
                            "outer_bits": fsm_result.outer_bits,
                            "bit_analysis": [{"bit_position": b.bit_position, "value": b.value, "description": b.description} for b in fsm_result.bit_analysis] if fsm_result.bit_analysis else [],
                            "energy_focus": {"focus_bit": fsm_result.energy_focus.focus_bit, "focus_description": fsm_result.energy_focus.focus_description},
                            "stress_analysis": {"stress_type": fsm_result.stress_analysis.stress_type, "analysis": fsm_result.stress_analysis.analysis},
                            "mutation_suggestion": fsm_result.mutation_suggestion,
                            "target_hexagram": fsm_result.target_hexagram,
                            "hexagram_reason": fsm_result.hexagram_reason,
                            "referenced_yao": fsm_result.referenced_yao,
                            "yao_interpretation": fsm_result.yao_interpretation,
                        }
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.session_state.messages = []
                    st.session_state.view = 'home'
                    st.rerun()

        # 侧边栏
        with st.sidebar:
            st.markdown('<div style="font-size:16px;font-weight:600;padding:20px 0;text-align:center;">☯ 枢机</div>', unsafe_allow_html=True)
            try:
                client = get_db_client()
                st.metric("知识库", f"{client.get_count():,}", "条记录")
            except:
                st.caption("⚠️ 数据库未连接")
            if st.button("⊕ 新对话", use_container_width=True):
                st.session_state.messages = []
                st.session_state.view = 'home'
                st.rerun()

        # 顶部导航
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown('<div style="font-size:20px;font-weight:600;letter-spacing:0.2em;">史易枢机</div>', unsafe_allow_html=True)
        with col2:
            if st.button("← 返回"):
                st.session_state.view = 'home'
                st.rerun()
        st.markdown("---")

        st.markdown('<div class="analysis-view">', unsafe_allow_html=True)

        # 渲染消息
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div style="background:var(--bg-surface);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px 24px;margin:16px 0;"><div style="font-size:11px;color:#71717A;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">输入</div><div style="font-size:16px;line-height:1.6;">{msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                if msg.get("retrieval_results"):
                    render_retrieval_results(msg["retrieval_results"])
                if msg.get("fsm_analysis"):
                    render_fsm_section(msg["fsm_analysis"])

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
