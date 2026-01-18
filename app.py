import streamlit as st
import math

# ================= CONFIG =================
st.set_page_config(
    page_title="MediaLive Configurator PRO",
    layout="wide",
    page_icon="🟣"
)

# ================= STYLE =================
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top, #12182b, #0b0f1a);
    color: #E6E8FF;
}
.block-container { padding: 2rem; }

.glass {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    border-radius: 18px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 40px rgba(124,124,255,0.08);
    margin-bottom: 20px;
}

.neon { color: #7C7CFF; font-weight: 600; }

.badge-ok {
    background: rgba(45,255,179,0.15);
    color: #2DFFB3;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 13px;
}

.badge-warn {
    background: rgba(255,92,92,0.15);
    color: #FF5C5C;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div class="glass">
<h1 class="neon">MediaLive Configurator PRO</h1>
<p>Professional LED Screen Engineering System</p>
</div>
""", unsafe_allow_html=True)

# ================= DATA =================
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20,
    "VX16S": 16, "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10,
    "VC16": 16, "VC24": 24, "MCTRL300": 2, "MCTRL600": 4,
    "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

CARD_MAX_PIXELS = {
    "A5s Plus": 320*256, "A7s Plus": 512*256, "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512, "MRV412": 512*512,
    "MRV416": 512*384, "MRV432": 512*512, "MRV532": 512*512,
    "NV3210": 512*384, "MRV208-N / MRV208-1": 256*256,
    "MRV470-1": 512*384, "A4s Plus": 256*256
}

INDOOR_PITCHES = [0.8,1.0,1.25,1.37,1.53,1.66,1.86,2.0,2.5,3.07,4.0]
OUTDOOR_PITCHES = [2.5,3.07,4.0,5.0,6.0,6.66,8.0,10.0]

# ================= SESSION =================
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2160

# ================= INPUT =================
st.markdown('<div class="glass">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("📐 Геометрия")
    width_mm = st.number_input("Ширина экрана (мм)", 320, step=320, value=st.session_state.width_mm)
    height_mm = st.number_input("Высота экрана (мм)", 160, step=160, value=st.session_state.height_mm)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"])

with col2:
    st.subheader("🧩 Конструкция")
    mount_type = st.radio("Тип монтажа", ["Монолитный", "В кабинетах"])
    tech = st.selectbox("Технология", ["SMD", "COB", "GOB"])
    pixel_pitch = st.selectbox("Шаг пикселя", INDOOR_PITCHES if screen_type=="Indoor" else OUTDOOR_PITCHES)

with col3:
    st.subheader("🎮 Система")
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"])
    processor = st.selectbox("Процессор", list(PROCESSOR_PORTS.keys()))
    receiving_card = st.selectbox("Receiving card", list(CARD_MAX_PIXELS.keys()))

with col4:
    st.subheader("⚡ Электрика")
    psu_power = st.selectbox("Мощность БП (Вт)", [200,300,400])
    power_reserve = st.selectbox("Запас питания (%)", [15,30])
    power_phase = st.radio("Сеть", ["220В (1 фаза)", "380В (3 фазы)"])

st.markdown('</div>', unsafe_allow_html=True)

# ================= CALC =================
modules_w = math.ceil(width_mm/320)
modules_h = math.ceil(height_mm/160)
real_w = modules_w * 320
real_h = modules_h * 160
total_modules = modules_w * modules_h

total_px = (real_w/pixel_pitch)*(real_h/pixel_pitch)

avg_power_module = 8 if screen_type=="Indoor" else 15
max_power_module = 24 if screen_type=="Indoor" else 45

avg_power = total_modules * avg_power_module / 1000
peak_power = total_modules * max_power_module / 1000
power_with_reserve = peak_power * (1+power_reserve/100)

num_psu = math.ceil(power_with_reserve / (psu_power/1000))
num_cards = math.ceil(total_px / CARD_MAX_PIXELS[receiving_card])

required_ports = math.ceil(total_px / 650000)
available_ports = PROCESSOR_PORTS[processor]
port_load = total_px/(available_ports*650000)*100

# ================= REPORT =================
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader("📊 Инженерный отчёт")

c1,c2,c3,c4 = st.columns(4)

c1.metric("Размер", f"{real_w} × {real_h} мм")
c2.metric("Разрешение", f"{int(real_w/pixel_pitch)} × {int(real_h/pixel_pitch)} px")
c3.metric("Модули", f"{total_modules} шт")
c4.metric("Площадь", f"{real_w*real_h/1_000_000:.2f} м²")

st.divider()

c1.metric("Средняя мощность", f"{avg_power:.1f} кВт")
c2.metric("Пиковая мощность", f"{peak_power:.1f} кВт")
c3.metric("С запасом", f"{power_with_reserve:.1f} кВт")
c4.metric("БП", f"{num_psu} шт")

st.divider()

c1.metric("Receiving cards", f"{num_cards} шт")
c2.metric("Процессор", processor)
c3.metric("Порты", f"{required_ports}/{available_ports}")
c4.metric("Нагрузка", f"{port_load:.1f}%")

if port_load < 85:
    st.markdown('<span class="badge-ok">Порты в норме</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="badge-warn">Перегруз портов</span>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ================= FOOTER =================
st.markdown("""
<div style="text-align:center; opacity:0.4; margin-top:40px">
MediaLive Configurator PRO • Engineering Edition
</div>
""", unsafe_allow_html=True)
