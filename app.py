import streamlit as st
import math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="LED Calculator Qiangli 320×160",
    page_icon="🟩",
    layout="wide"
)

# =========================
# CONSTANTS
# =========================

MODULE_W = 320
MODULE_H = 160

SPECS = {
    "Indoor": {
        "max_w": 24,
        "avg_w": 8,
        "weight": 0.37,
        "current": 5.2,
        "brightness": "800–1800 нит"
    },
    "Outdoor": {
        "max_w": 40,
        "avg_w": 13,
        "weight": 0.42,
        "current": 9.2,
        "brightness": "4500–8000 нит"
    }
}

INDOOR_PITCHES = [0.8,1.0,1.25,1.37,1.53,1.66,1.86,2.0,2.5,3.07,4.0]
OUTDOOR_PITCHES = [2.5,3.07,4.0,5.0,6.0,6.66,8.0,10.0]

NOVASTAR_CARDS = {
    "A5s Plus": (320,256),
    "A7s Plus": (512,256),
    "A8s / A8s-N": (512,384),
    "A10s Pro": (512,512),
    "MRV412": (512,512),
    "MRV416": (512,384),
    "MRV432": (512,512),
    "MRV532": (512,512),
    "NV3210": (512,384),
    "MRV208": (256,256),
    "MRV470": (512,384),
    "A4s Plus": (256,256),
}

# =========================
# UI HEADER
# =========================

st.title("🟩 Профессиональный калькулятор LED экранов Qiangli 320×160 (Novastar)")
st.caption("Инженерный расчёт | Электрика | Управление | Вес | PDF отчёт")

st.divider()

# =========================
# INPUT PANEL
# =========================

colA, colB = st.columns(2)

with colA:
    st.subheader("📐 Геометрия экрана")

    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=3200)
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=1920)

    modules_x = math.ceil(width_mm / MODULE_W)
    modules_y = math.ceil(height_mm / MODULE_H)
    modules = modules_x * modules_y

    st.success(f"Модули: {modules_x} × {modules_y} = {modules} шт")
    st.info(f"Реальный размер: {modules_x*MODULE_W} × {modules_y*MODULE_H} мм")

with colB:
    st.subheader("🖥 Тип экрана")

    screen_type = st.selectbox("Тип экрана", ["Indoor", "Outdoor"])
    pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES if screen_type=="Indoor" else OUTDOOR_PITCHES)
    refresh = st.selectbox("Частота обновления (Hz)", [1920,2880,3840,6000,7680])

    if refresh >= 6000:
        st.warning("Высокая нагрузка на процессор при 6000+ Hz")

# =========================
# POWER
# =========================

st.divider()
st.subheader("⚡ Электропитание")

col1, col2, col3 = st.columns(3)

with col1:
    psu_power = st.selectbox("Мощность блока питания (Вт)", [200,300,400])
    psu_modules = st.selectbox("Модулей на БП", [4,6,8,10], index=2)

with col2:
    margin = st.selectbox("Запас по питанию", ["15%", "30%"], index=1)
    margin_factor = 1.15 if margin=="15%" else 1.30

with col3:
    reserve = st.checkbox("Резервные модули (5%)", value=False)

# =========================
# CONTROL
# =========================

st.divider()
st.subheader("🎛 Управление Novastar")

col4, col5 = st.columns(2)

with col4:
    card_model = st.selectbox("Принимающая карта", list(NOVASTAR_CARDS.keys()))
    modules_per_card = st.selectbox("Модулей на карту", [8,10,12,16], index=0)

with col5:
    system_type = st.selectbox("Тип системы", ["Синхронная", "Асинхронная"])
    processor = st.text_input("Процессор / плеер", "MCTRL4K" if system_type=="Синхронная" else "TB3")

# =========================
# CALCULATION
# =========================

spec = SPECS[screen_type]

module_max_w = spec["max_w"]
module_weight = spec["weight"]
module_current = spec["current"]

total_power_max = modules * module_max_w * margin_factor
total_power_avg = modules * spec["avg_w"]

psu_count = max(
    math.ceil(total_power_max / psu_power),
    math.ceil(modules / psu_modules)
)

if reserve:
    reserve_modules = math.ceil(modules * 0.05)
else:
    reserve_modules = 0

total_modules = modules + reserve_modules

# Pixels
px_w = int(MODULE_W / pitch)
px_h = int(MODULE_H / pitch)
res_w = modules_x * px_w
res_h = modules_y * px_h
total_pixels = res_w * res_h

card_px = NOVASTAR_CARDS[card_model][0] * NOVASTAR_CARDS[card_model][1]
cards_by_pixels = math.ceil(total_pixels / card_px)
cards_by_modules = math.ceil(modules / modules_per_card)
cards = max(cards_by_pixels, cards_by_modules)

# Processor ports
ports = math.ceil(total_pixels / 650000)
port_load = (total_pixels / (ports * 650000)) * 100

# Weight
area = (modules_x * 0.32) * (modules_y * 0.16)
weight_modules = modules * module_weight
total_weight = weight_modules * 1.05

# =========================
# OUTPUT
# =========================

st.divider()
st.subheader("📊 Результаты расчёта")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Модули", f"{total_modules} шт")
    st.metric("Площадь", f"{area:.2f} м²")

with c2:
    st.metric("Разрешение", f"{res_w} × {res_h}")
    st.metric("Пикселей", f"{total_pixels:,}")

with c3:
    st.metric("Пиковая мощность", f"{total_power_max/1000:.2f} кВт")
    st.metric("Средняя мощность", f"{total_power_avg/1000:.2f} кВт")

with c4:
    st.metric("БП", f"{psu_count} шт")
    st.metric("Карты", f"{cards} шт")

# Status
if port_load > 100:
    st.error("❌ Недостаточно портов процессора!")
elif port_load > 90:
    st.warning(f"⚠ Нагрузка порта {port_load:.1f}%")
else:
    st.success(f"✅ Нагрузка порта {port_load:.1f}%")

# =========================
# PDF EXPORT
# =========================

def generate_pdf():
    filename = f"LED_Raschet_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ПРОФЕССИОНАЛЬНЫЙ РАСЧЁТ LED ЭКРАНА QIANGLI 320×160", styles["Title"]))
    story.append(Spacer(1,20))

    data = [
        ["Параметр", "Значение"],
        ["Тип экрана", screen_type],
        ["Размер", f"{modules_x*320} × {modules_y*160} мм"],
        ["Разрешение", f"{res_w} × {res_h} px"],
        ["Площадь", f"{area:.2f} м²"],
        ["Модули", f"{total_modules} шт"],
        ["Шаг", f"P{pitch}"],
        ["Частота", f"{refresh} Hz"],
        ["Яркость", spec["brightness"]],
        ["Пиковая мощность", f"{total_power_max/1000:.2f} кВт"],
        ["БП", f"{psu_count} шт × {psu_power} Вт"],
        ["Карты Novastar", f"{cards} шт ({card_model})"],
        ["Процессор", processor],
        ["Вес", f"{total_weight:.1f} кг"],
    ]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003366")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))

    story.append(table)
    doc.build(story)
    return filename

st.divider()

if st.button("📄 Сформировать PDF отчёт"):
    pdf_file = generate_pdf()
    with open(pdf_file, "rb") as f:
        st.download_button("⬇ Скачать PDF", f, file_name=pdf_file)
