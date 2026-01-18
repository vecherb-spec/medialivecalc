# ================= MEDIA LIVE CONFIGURATOR PRO v4 =================
# Factory Engineering Edition
# Based 100% on original engineering core
# ================================================================

import streamlit as st
import math
import pandas as pd
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="MediaLive Configurator PRO v4",
    layout="wide",
    page_icon="🟣"
)

# ---------------- PRO THEME ----------------
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top, #0e1325, #070b17);
    color: #E6E8FF;
}
.glass {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 22px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 40px rgba(124,124,255,0.08);
    margin-bottom: 20px;
}
.title {
    font-size: 38px;
    font-weight: 700;
    color: #7C7CFF;
}
.subtitle {
    opacity: 0.6;
}
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #7C7CFF, transparent);
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="glass">
  <div class="title">MediaLive Configurator PRO v4</div>
  <div class="subtitle">Factory Engineering Edition • Qiangli • Novastar</div>
</div>
""", unsafe_allow_html=True)

# ===================== ENGINEERING DATA =====================
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
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

# ===================== SIDEBAR NAV =====================
menu = st.sidebar.radio(
    "Навигация PRO",
    [
        "Проект",
        "Геометрия",
        "Конструкция",
        "Электрика",
        "Система",
        "Коммутация",
        "Логистика",
        "Инженерный отчёт"
    ]
)

# ===================== PROJECT =====================
if menu == "Проект":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("📁 Паспорт проекта")

    project = st.text_input("Проект", "MediaLive LED Screen")
    client = st.text_input("Клиент")
    location = st.text_input("Локация")
    engineer = st.text_input("Инженер", "MediaLive Engineering")
    date = st.date_input("Дата", datetime.now())

    mount_type = st.radio("Тип монтажа", ["Монолитный", "В кабинетах"])
    installation = st.radio("Установка", ["Стена", "Подвес", "Напольная"])

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== GEOMETRY =====================
if menu == "Геометрия":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("📐 Геометрия экрана")

    col1, col2, col3 = st.columns(3)

    with col1:
        width_mm = st.number_input("Ширина экрана (мм)", 320, step=320, value=3840)
        height_mm = st.number_input("Высота экрана (мм)", 160, step=160, value=2160)
        screen_type = st.radio("Тип экрана", ["Indoor","Outdoor"])

    with col2:
        pixel_pitch = st.selectbox(
            "Шаг пикселя (мм)",
            INDOOR_PITCHES if screen_type=="Indoor" else OUTDOOR_PITCHES,
            index=8 if screen_type=="Indoor" else 0
        )
        tech = st.selectbox("Технология", ["SMD","COB","GOB"])

    with col3:
        refresh_rate = st.selectbox("Частота обновления (Hz)", [1920,2880,3840,6000,7680], index=2)

    modules_w = math.ceil(width_mm/320)
    modules_h = math.ceil(height_mm/160)
    real_w = modules_w * 320
    real_h = modules_h * 160

    res_w = int(real_w / pixel_pitch)
    res_h = int(real_h / pixel_pitch)
    area = real_w * real_h / 1_000_000

    st.markdown("---")
    st.metric("Фактический размер", f"{real_w} × {real_h} мм")
    st.metric("Разрешение", f"{res_w} × {res_h} px")
    st.metric("Площадь", f"{area:.2f} м²")

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== SYSTEM =====================
if menu == "Система":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("🧠 Система управления")

    system_type = st.radio("Тип системы", ["Синхронный","Асинхронный"])
    processors = (
        ["VC2","VC4","VC6","VC10","VC16","VC24","MCTRL300","MCTRL600","MCTRL700","MCTRL4K","MCTRL R5",
         "VX400","VX600 Pro","VX1000 Pro","VX2000 Pro","VX16S"]
        if system_type=="Синхронный"
        else ["TB10 Plus","TB30","TB40","TB50","TB60"]
    )

    processor = st.selectbox("Процессор / Плеер", processors)
    receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()))

    total_px = (real_w/pixel_pitch)*(real_h/pixel_pitch)
    req_ports = math.ceil(total_px/650000)
    avail_ports = PROCESSOR_PORTS[processor]
    load = total_px/(avail_ports*650000)*100

    st.markdown(f"""
    **Порты:** {avail_ports}  
    **Требуется:** {req_ports}  
    **Нагрузка:** {load:.1f}%
    """)

    if load > 90:
        st.warning("⚠️ Нагрузка портов >90%")

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== ELECTRICAL =====================
if menu == "Электрика":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("⚡ Электропитание")

    psu_power = st.selectbox("Блок питания (Вт)", [200,300,400])
    reserve = st.radio("Запас по питанию (%)", [15,30], index=1)
    phase = st.radio("Сеть", ["220 В","380 В"])

    avg_mod = 8 if screen_type=="Indoor" else 15
    max_mod = 24 if screen_type=="Indoor" else 45

    total_modules = modules_w * modules_h
    peak_kw = total_modules * max_mod / 1000
    power_kw = peak_kw * (1 + reserve/100)

    psu_kw = psu_power/1000
    psu_qty = math.ceil(power_kw/psu_kw)

    voltage = 220 if phase=="220 В" else 380*math.sqrt(3)
    current = power_kw*1000/voltage
    breaker = math.ceil(current*1.25)

    st.markdown(f"""
    **Модулей:** {total_modules}  
    **Пиковая мощность:** {peak_kw:.1f} кВт  
    **С запасом:** {power_kw:.1f} кВт  
    **БП:** {psu_qty} шт  
    **Ток:** {current:.1f} А  
    **Автомат:** {breaker} А
    """)

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== LOGISTICS =====================
if menu == "Логистика":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("🚚 Логистика и вес")

    module_weight = 0.37 if screen_type=="Indoor" else 0.5
    weight_modules = total_modules * module_weight
    weight_total = weight_modules * 1.05

    boxes = math.ceil(total_modules/40)
    volume = boxes * 0.06

    st.markdown(f"""
    **Вес модулей:** {weight_modules:.1f} кг  
    **Общий вес:** {weight_total:.1f} кг  
    **Коробки:** {boxes} шт  
    **Объём:** {volume:.2f} м³
    """)

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== FINAL REPORT =====================
if menu == "Инженерный отчёт":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("📘 Финальный инженерный отчёт")

    st.markdown(f"""
### Проект
- **Проект:** {project}
- **Клиент:** {client}
- **Локация:** {location}

### Экран
- **Размер:** {real_w} × {real_h} мм
- **Разрешение:** {res_w} × {res_h} px
- **Площадь:** {area:.2f} м²
- **Шаг пикселя:** {pixel_pitch} мм
- **Частота:** {refresh_rate} Hz

### Система
- **Процессор:** {processor}
- **Receiving card:** {receiving_card}

### Электрика
- **Мощность:** {power_kw:.1f} кВт
- **БП:** {psu_qty} шт
- **Автомат:** {breaker} А

### Логистика
- **Вес:** {weight_total:.1f} кг
- **Объём:** {volume:.2f} м³
""")

    st.success("MediaLive Configurator PRO v4 — расчёт завершён")
    st.markdown('</div>', unsafe_allow_html=True)
