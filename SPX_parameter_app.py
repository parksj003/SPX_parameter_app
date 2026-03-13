import streamlit as st
import numpy as np
import math
from scipy.interpolate import interp1d

# 페이지 설정
st.set_page_config(page_title="Laser Precision Dashboard", layout="wide")

# 스타일 설정 (가독성 및 빨간색 소수점 포인트)
st.markdown("""
    <style>
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th { background-color: #262730; color: white; text-align: left; padding: 12px; font-size: 0.9em; }
    td { padding: 10px; border-bottom: 1px solid #444; font-size: 0.95em; }
    .main-val { font-weight: bold; font-size: 1.05em; }
    .raw-val { color: #ff4b4b; font-size: 0.8em; font-weight: normal; margin-left: 5px; }
    
    /* 하단 요약 박스 (고대비 커스텀) */
    .summary-box {
        background-color: #111111;
        color: #eeeeee;
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #ff4b4b;
        margin-top: 25px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .summary-title { color: #ff4b4b; font-weight: bold; font-size: 1.2em; margin-bottom: 8px; }
    .highlight { color: #00d4ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Laser Parameter Precision Dashboard")

# --- 1. 데이터 정의 ---
power_pct = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
power_200khz = np.array([0.25, 1.0, 2.0, 3.2, 4.6, 6.4, 8.2, 9.8, 10.5, 10.4])
power_1000khz = np.array([0.05, 0.1, 0.3, 0.5, 0.8, 1.2, 1.7, 2.1, 2.7, 3.3])

f_200 = interp1d(power_pct, power_200khz, fill_value="extrapolate")
f_1000 = interp1d(power_pct, power_1000khz, fill_value="extrapolate")

def get_actual_power(rep_khz, set_pct):
    weight = (rep_khz - 200) / (1000 - 200)
    actual_w = f_200(set_pct) + weight * (f_1000(set_pct) - f_200(set_pct))
    return max(0.01, float(actual_w))

# --- 2. 공통 설정 (펄스 범위) ---
with st.expander("📝 공통 펄스 범위 설정", expanded=True):
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1: min_p = st.number_input("Min Pulse", value=1, step=1)
    with c_p2: max_p = st.number_input("Max Pulse", value=10, step=1)
    with c_p3: count_p = st.number_input("Steps", value=5, step=1)

pulse_list = np.linspace(min_p, max_p, int(count_p))

# --- 3. Mode 1 & Mode 2 병렬 배치 ---
col_left, col_right = st.columns(2)

# --- Mode 1 Section ---
with col_left:
    st.subheader("📍 Mode 1: Base Setting")
    rep_m1 = st.select_slider("M1 Rep (kHz)", options=[200, 300, 400, 500, 600, 700, 800, 900, 1000], value=200, key="r1")
    pwr_m1 = st.slider("M1 Power (%)", 10, 100, 80, key="p1")
    
    html_m1 = "<table><tr><th>Pulse</th><th>Interval (μs)</th><th>Max Freq (kHz)</th></tr>"
    for p in pulse_list:
        raw_int = ((p + 1) * 1000 / rep_m1) + 8
        ceil_int = math.ceil(raw_int)
        max_k = 1000 / ceil_int
        html_m1 += f"<tr><td>{int(p)}</td><td><span class='main-val'>{ceil_int}</span><span class='raw-val'>({raw_int:.2f})</span></td><td>{max_k:.3f}</td></tr>"
    st.markdown(html_m1 + "</table>", unsafe_allow_html=True)

# --- Mode 2 Section ---
with col_right:
    st.subheader("⚖️ Mode 2: Compensated")
    rep_m2 = st.select_slider("M2 Rep (kHz)", options=[200, 300, 400, 500, 600, 700, 800, 900, 1000], value=1000, key="r2")
    pwr_m2 = st.slider("M2 Power (%)", 10, 100, 50, key="p2")
    
    w_m1 = get_actual_power(rep_m1, pwr_m1)
    w_m2 = get_actual_power(rep_m2, pwr_m2)
    comp_ratio = w_m1 / w_m2
    
    html_m2 = "<table><tr><th>Adj. Pulse</th><th>Interval (μs)</th><th>Max Freq (kHz)</th></tr>"
    for p in pulse_list:
        raw_adj = p * comp_ratio
        ceil_adj = math.ceil(raw_adj)
        raw_int_m2 = ((ceil_adj + 1) * 1000 / rep_m2) + 8
        ceil_int_m2 = math.ceil(raw_int_m2)
        max_k_m2 = 1000 / ceil_int_m2
        
        html_m2 += f"""<tr>
            <td><span class='main-val'>{ceil_adj}</span><span class='raw-val'>({raw_adj:.2f})</span></td>
            <td><span class='main-val'>{ceil_int_m2}</span><span class='raw-val'>({raw_int_m2:.2f})</span></td>
            <td>{max_k_m2:.3f}</td>
        </tr>"""
    st.markdown(html_m2 + "</table>", unsafe_allow_html=True)

# --- 하단 요약 정보 (고대비 및 독립 변수 반영) ---
st.markdown(f"""
<div class="summary-box">
    <div class="summary-title">📊 Power Analysis Summary</div>
    각 모드의 설정값에 따른 분석 결과입니다:<br>
    • <b>Mode 1</b> ({rep_m1}kHz / {pwr_m1}%): <span class="highlight">{w_m1:.2f}W</span> (기준 출력)<br>
    • <b>Mode 2</b> ({rep_m2}kHz / {pwr_m2}%): <span class="highlight">{w_m2:.2f}W</span> (보정 전 1펄스 당 출력)<br>
    • <b>동일 출력 유지를 위한 보정 배율:</b> <span class="highlight" style="font-size: 1.25em;">{comp_ratio:.3f}x</span>
</div>
""", unsafe_allow_html=True)
