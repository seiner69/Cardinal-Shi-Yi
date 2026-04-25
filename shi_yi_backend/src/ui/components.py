"""UI组件"""

import streamlit as st
from src.data.hexagrams import HEXAGRAM_DATA


def _get_hex_info(inner_bits, outer_bits):
    from src.llm.chain import get_hexagram_info
    return get_hexagram_info(inner_bits, outer_bits)


def _status_class(t):
    if "断裂" in t: return "danger"
    if "撞墙" in t: return "warning"
    return "success"


def render_fsm_section(fsm):
    if not fsm:
        return

    inner = fsm.get('inner_bits', '???')
    outer = fsm.get('outer_bits', '???')
    target = fsm.get('target_hexagram', '')
    stress = fsm.get('stress_analysis', {})
    stress_type = stress.get('stress_type', '稳定')
    focus = fsm.get('energy_focus', {})
    focus_bit = focus.get('focus_bit', '?')
    sc = _status_class(stress_type)
    tgt = HEXAGRAM_DATA.get(target, {}) if target else {}

    # 01 参照系划定
    with st.expander("01 参照系划定", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="hex-card" style="padding:20px;"><div class="hex-meta">内系统</div><div style="font-size:14px;color:#A1A1AA;">{fsm.get("inner_system", "—")}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="hex-card" style="padding:20px;"><div class="hex-meta">外系统</div><div style="font-size:14px;color:#A1A1AA;">{fsm.get("outer_system", "—")}</div></div>', unsafe_allow_html=True)

    # 02 提取机器码
    info = _get_hex_info(inner, outer)
    name = info.get("hexagram", "")
    data = HEXAGRAM_DATA.get(name, {}) if name else {}

    with st.expander("02 提取机器码", expanded=True):
        st.markdown(f'<div class="bit-row"><div class="bit-group"><div class="bit-label">Inner</div><div class="bit-value inner">{inner}</div></div><div class="bit-group"><div class="bit-label">Outer</div><div class="bit-value outer">{outer}</div></div></div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="hex-card main">
            <div class="hex-symbol">{data.get("symbol", "☰")}</div>
            <div class="hex-name">{name}卦</div>
            <div class="hex-meta">{info.get("outer_trigram", "")}上 {info.get("inner_trigram", "")}下</div>
            <div class="hex-quote">「{data.get("gua_ci", "")}」</div>
        </div>
        ''', unsafe_allow_html=True)

        cols = st.columns(3)
        for i, bit in enumerate(fsm.get('bit_analysis', [])):
            vc = "v1" if bit.get('value') == "1" else "v0"
            with cols[i % 3]:
                st.markdown(f'<div class="hex-card" style="padding:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><span style="font-size:11px;color:#71717A;">Bit {bit.get("bit_position", "?")}</span><span style="font-size:18px;font-weight:600;font-family:monospace;color:{"#63B3ED" if vc=="v1" else "#A1A1AA"};">{bit.get("value", "?")}</span></div><div style="font-size:12px;color:#71717A;">{bit.get("description", "")}</div></div>', unsafe_allow_html=True)

    # 03 场域力学分析（包含状态概览）
    with st.expander("03 场域力学分析", expanded=True):
        # 状态行
        st.markdown('<div class="status-row">', unsafe_allow_html=True)
        st.markdown(f'<div class="status-card"><div class="status-label">应力状态</div><div class="status-value {sc}">{stress_type}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-card"><div class="status-label">能量焦点</div><div class="status-value" style="color:#63B3ED;">Bit {focus_bit}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-card"><div class="status-label">当前码</div><div class="status-value" style="font-size:14px;">{inner}|{outer}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 状态面板
        st.markdown(f'<div class="status-panel {sc}"><div style="font-weight:600;margin-bottom:8px;">{stress_type} <span style="font-size:11px;font-family:monospace;background:#131316;padding:4px 8px;border-radius:4px;margin-left:8px;">Bit {focus_bit}</span></div><div style="font-size:13px;color:#A1A1AA;margin-bottom:8px;">核心症结：{focus.get("focus_description", "—")}</div><div style="font-size:14px;line-height:1.6;color:#71717A;">{stress.get("analysis", "—")}</div></div>', unsafe_allow_html=True)

    # 04 变爻与演化（包含目标卦象）
    mut = fsm.get('mutation_suggestion', '—')
    yao = fsm.get('yao_interpretation', '—')
    ref = fsm.get('referenced_yao', '')

    with st.expander("04 变爻与演化", expanded=True):
        st.markdown(f'<div class="strategy-card"><div class="strategy-label">策略推演</div><div style="font-size:14px;line-height:1.6;color:#A1A1AA;">{mut}</div></div>', unsafe_allow_html=True)
        if ref:
            st.markdown(f'<div class="strategy-card" style="margin-top:12px;background:rgba(139,92,246,0.05);"><div class="strategy-label" style="color:#22D3EE;">爻辞引用</div><div style="font-size:14px;line-height:1.6;color:#A1A1AA;">{ref}</div></div>', unsafe_allow_html=True)
        if yao:
            st.markdown(f'<div class="strategy-card" style="margin-top:12px;"><div class="strategy-label">易理映射</div><div style="font-size:14px;line-height:1.6;color:#A1A1AA;">{yao}</div></div>', unsafe_allow_html=True)

        # 目标卦象
        st.markdown(f'''
        <div class="hex-card" style="margin-top:24px;">
            <div class="hex-meta" style="color:#63B3ED;">目标卦象</div>
            <div class="hex-symbol">{tgt.get("symbol", "☰")}</div>
            <div class="hex-name">{target}卦</div>
            <div class="hex-meta">第 {tgt.get("index", "?")} 卦</div>
            <div class="hex-quote">「{tgt.get("gua_ci", "")}」</div>
        </div>
        ''', unsafe_allow_html=True)


def render_retrieval_results(results):
    if not results:
        return
    st.markdown('<div class="sources-title">参考典籍</div>', unsafe_allow_html=True)
    for r in results:
        h = r.get('hexagram_name', '')
        sym = HEXAGRAM_DATA.get(h, {}).get('symbol', '☰') if h in HEXAGRAM_DATA else '☰'
        ctx = r.get('context', r.get('content', ''))
        st.markdown(f'<div class="source-item"><div class="source-meta">{sym} {h} · {r.get("text_type", "")}</div><div class="source-text">{ctx[:160]}{"..." if len(ctx)>160 else ""}</div></div>', unsafe_allow_html=True)


def render_loading():
    st.markdown('''
    <div style="display:flex;flex-direction:column;align-items:center;padding:48px;">
        <div style="display:flex;gap:8px;">
            <div style="width:8px;height:8px;background:#63B3ED;border-radius:50%;animation:pulse 1.2s infinite;"></div>
            <div style="width:8px;height:8px;background:#A78BFA;border-radius:50%;animation:pulse 1.2s infinite;animation-delay:-0.2s;"></div>
            <div style="width:8px;height:8px;background:#22D3EE;border-radius:50%;animation:pulse 1.2s infinite;animation-delay:-0.4s;"></div>
        </div>
        <div style="margin-top:24px;font-size:13px;color:#71717A;">推演分析中</div>
    </div>
    <style>@keyframes pulse{0%,80%,100%{transform:scale(0.6);opacity:0.4}40%{transform:scale(1);opacity:1}}</style>
    ''', unsafe_allow_html=True)
