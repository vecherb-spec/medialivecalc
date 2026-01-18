import streamlit as st
import math
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="MediaLive LED Calculator V5", layout="wide", page_icon="🖥️")

st.markdown("""
<style>
.main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
h1, h2, h3 {color: #a78bfa !important;}
.stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border-radius: 12px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("🖥️ MediaLive LED Screen Calculator V5")
st.markdown("Промышленный инженерный калькулятор LED-экранов")

# ---------------- DATA ----------------
PROCESSOR_PORTS = {
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16,
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20
}

CARD_MAX_PIXELS = {
    "A5s Plus": 320*256,
    "A7s Plus": 512*256,
    "A8s": 512*384,
    "A10s Pro": 512*512,
    "MRV412": 512*512
}

INDOOR_PITCHES = [1.25, 1.53, 1.86, 2.0, 2.5, 3.07]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0]

# ---------------- INPUT ----------------
col1, col2, col3 = st.columns(3)

with col1:
    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=2240)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"])

with col2:
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES if screen_type=="Indoor" else OUTDOOR_PITCHES)
    refresh_rate = st.selectbox("Частота обновления", [1920, 2880, 3840, 7680], index=2)
    processor = st.selectbox("Процессор", list(PROCESSOR_PORTS.keys()))

with col3:
    receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()))
    psu_power = st.selectbox("Мощность БП (Вт)", [200,300,400], index=1)
    power_reserve = st.radio("Запас по питанию", [15,30], index=1)

# ---------------- CALCULATION ----------------
if st.button("🔧 Рассчитать проект", use_container_width=True):

    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    total_modules = modules_w * modules_h

    real_width = modules_w * 320
    real_height = modules_h * 160

    resolution_w = int(real_width / pixel_pitch)
    resolution_h = int(real_height / pixel_pitch)
    total_pixels = resolution_w * resolution_h

    avg_power_module = 8 if screen_type=="Indoor" else 15
    max_power_module = 24 if screen_type=="Indoor" else 45

    avg_power = total_modules * avg_power_module / 1000
    peak_power = total_modules * max_power_module / 1000
    power_with_reserve = peak_power * (1 + power_reserve/100)

    num_psu = math.ceil(power_with_reserve / (psu_power/1000))

    max_pixels_card = CARD_MAX_PIXELS[receiving_card]
    num_cards = math.ceil(total_pixels / max_pixels_card)

    required_ports = math.ceil(total_pixels / 650000)
    available_ports = PROCESSOR_PORTS[processor]

    # ---------------- REPORT DATA ----------------
    report = {
        "Ширина экрана (мм)": real_width,
        "Высота экрана (мм)": real_height,
        "Разрешение": f"{resolution_w} x {resolution_h}",
        "Площадь (м²)": round(real_width*real_height/1_000_000,2),
        "Шаг пикселя": pixel_pitch,
        "Частота": refresh_rate,
        "Модулей всего": total_modules,
        "Средняя мощность (кВт)": round(avg_power,2),
        "Пиковая мощность (кВт)": round(peak_power,2),
        "Мощность с запасом (кВт)": round(power_with_reserve,2),
        "Блоки питания (шт)": num_psu,
        "Принимающие карты (шт)": num_cards,
        "Процессор": processor,
        "Необходимых портов": required_ports,
        "Доступно портов": available_ports
    }

    st.success("✅ Проект рассчитан")

    st.subheader("📊 Основные параметры")
    st.json(report)

    # ---------------- EXCEL EXPORT ----------------
    df = pd.DataFrame(list(report.items()), columns=["Параметр","Значение"])
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name="MediaLive Report")
    excel_buffer.seek(0)

    # ---------------- PDF EXPORT ----------------
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph("MediaLive LED Screen Project Report", styles["Title"]))
    elements.append(Spacer(1,12))

    table_data = [["Параметр","Значение"]]
    for k,v in report.items():
        table_data.append([k,str(v)])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")
    ]))

    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)

    # ---------------- DOWNLOAD BUTTONS ----------------
    colx, coly = st.columns(2)

    with colx:
        st.download_button(
            "📥 Скачать Excel спецификацию",
            data=excel_buffer,
            file_name="MediaLive_LED_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with coly:
        st.download_button(
            "📄 Скачать PDF отчёт",
            data=pdf_buffer,
            file_name="MediaLive_LED_Report.pdf",
            mime="application/pdf"
        )
