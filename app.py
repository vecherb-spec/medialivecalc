import streamlit as st
import math
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ================= CONFIG =================

st.set_page_config(
    page_title="LED Engineer Calculator v4",
    page_icon="🟩",
    layout="wide"
)

# ================= CONSTANTS =================

MODULE_W = 320
MODULE_H = 160

QIANGLI = {
    "Indoor": {"max_w":24,"avg_w":8,"weight":0.37,"current":5.2},
    "Outdoor": {"max_w":40,"avg_w":13,"weight":0.42,"current":9.2}
}

CABINETS = {
    "QM Series (640×480, ~20кг)": (640,480,20),
    "MG Series (960×960, ~40кг)": (960,960,40),
    "QF Series (500×500, ~13.5кг)": (500,500,13.5),
    "QS Series (960×960, ~45кг)": (960,960,45),
    "Custom": None
}

NOVASTAR = {
    "A5s Plus":(320,256),
    "A7s Plus":(512,256),
    "A8s-N":(512,384),
    "A10s Pro":(512,512),
    "MRV412":(512,512),
    "MRV416":(512,384),
    "MRV432":(512,512),
    "MRV532":(512,512),
    "NV3210":(512,384),
    "MRV208":(256,256),
    "MRV470":(512,384),
    "A4s Plus":(256,256)
}

CABLES = [
    (16, "3×2.5 ВВГ"),
    (25, "3×4 ВВГ"),
    (32, "3×6 ВВГ"),
    (40, "3×10 ВВГ"),
    (63, "3×16 ВВГ")
]

# ================= HEADER =================

st.title("🟩 LED Engineer Calculator v4 — Qiangli / Dahua 320×160 + Novastar")
st.caption("Проектировочный конфигуратор LED-систем (инженерный уровень)")
st.divider()

# ================= INPUT =================

col1, col2, col3 = st.columns(3)

with col1:
    width = st.number_input("Ширина экрана (мм)",320,50000,3200,320)
    height = st.number_input("Высота экрана (мм)",160,50000,1920,160)

    mx = math.ceil(width / MODULE_W)
    my = math.ceil(height / MODULE_H)
    modules = mx * my

    real_w = mx * MODULE_W
    real_h = my * MODULE_H

    st.success(f"Реальный размер: {real_w} × {real_h} мм")
    st.info(f"Модули: {modules} шт")

with col2:
    screen_type = st.selectbox("Тип экрана",["Indoor","Outdoor"])
    pitch = st.selectbox("Шаг пикселя (мм)",[0.8,1.25,1.53,2.5,3.07,4.0,5.0,6.66,8.0])
    refresh = st.selectbox("Частота обновления (Hz)",[1920,2880,3840,6000,7680])
    tech = st.selectbox("Технология модуля",["SMD","COB","GOB"])

with col3:
    mount_type = st.selectbox("Тип монтажа",["В кабинетах","Монолитный"])
    reserve = st.selectbox("Резерв модулей",["0%","3%","5%","10%"])
    sensor = st.selectbox("Датчик яркости/температуры",["Нет","NSO60"])

# ================= CABINETS / MONOLITH =================

st.divider()

if mount_type == "В кабинетах":
    cabinet_model = st.selectbox("Модель кабинета Qiangli", list(CABINETS.keys()))
    if cabinet_model == "Custom":
        cab_w = st.number_input("Ширина кабинета (мм)",300,2000,640)
        cab_h = st.number_input("Высота кабинета (мм)",300,2000,480)
        cab_weight = st.number_input("Вес кабинета (кг)",5.0,100.0,20.0)
    else:
        cab_w, cab_h, cab_weight = CABINETS[cabinet_model]
else:
    magnet = st.selectbox("Размер магнита",["10 мм","13 мм","17 мм"])

# ================= CONTROL =================

st.divider()

system_type = st.selectbox("Тип системы",["Синхронная","Асинхронная"])
card_model = st.selectbox("Принимающая карта Novastar", list(NOVASTAR.keys()))
modules_per_card = st.selectbox("Модулей на карту",[8,10,12,16])

if system_type == "Синхронная":
    processor = st.selectbox("Процессор Novastar",["VC6","VC10","MCTRL4K","VX1000"])
else:
    processor = st.selectbox("Плеер TB",["TB1","TB3","TB8"])

# ================= POWER =================

st.divider()

psu_power = st.selectbox("Мощность БП (Вт)",[200,300,400])
modules_per_psu = st.selectbox("Модулей на БП",[4,6,8,10])
phases = st.selectbox("Тип сети",["220В (1 фаза)","380В (3 фазы)"])

# ================= CALC =================

spec = QIANGLI[screen_type]

# Pixels
px_w = int(320 / pitch)
px_h = int(160 / pitch)
res_w = mx * px_w
res_h = my * px_h
pixels = res_w * res_h

# Power
peak_power = modules * spec["max_w"] * 1.3
avg_power = modules * spec["avg_w"]

psu_count = max(
    math.ceil(peak_power / psu_power),
    math.ceil(modules / modules_per_psu)
)

# Cards
card_px = NOVASTAR[card_model][0] * NOVASTAR[card_model][1]
cards = max(
    math.ceil(pixels / card_px),
    math.ceil(modules / modules_per_card)
)

# Ports
ports = math.ceil(pixels / 650000)
port_load = pixels / (ports * 650000) * 100

# Weight
area = (real_w/1000) * (real_h/1000)
weight_modules = modules * spec["weight"]

if mount_type == "В кабинетах":
    cabinets_x = math.ceil(real_w / cab_w)
    cabinets_y = math.ceil(real_h / cab_h)
    cabinet_count = cabinets_x * cabinets_y
    frame_weight = cabinet_count * cab_weight
else:
    frame_weight = area * 2

total_weight = (weight_modules + frame_weight) * 1.05

# Reserve
reserve_factor = {"0%":0,"3%":0.03,"5%":0.05,"10%":0.1}[reserve]
reserve_modules = math.ceil(modules * reserve_factor)
total_modules = modules + reserve_modules

# Electric
if phases.startswith("220"):
    voltage = 220
    current = peak_power / voltage
else:
    voltage = 380
    current = peak_power / (voltage * 1.73)

auto = "—"
cable = "—"
for amp, cname in CABLES:
    if current <= amp:
        auto = f"C{amp}"
        cable = cname
        break

# Packing
boxes = math.ceil(total_modules / 40)
packing_weight = boxes * 22
volume = boxes * 0.06

# ================= BOM =================

bom = [
    ["LED модули Qiangli 320×160", f"{total_modules} шт"],
    ["Блоки питания", f"{psu_count} шт"],
    ["Принимающие карты Novastar", f"{cards} шт ({card_model})"],
    ["Процессор/плеер", processor],
    ["Силовой кабель", cable],
    ["Автомат защиты", auto],
    ["Каркас/кабинеты", f"{frame_weight:.1f} кг"],
    ["Датчик", sensor],
    ["Упаковка", f"{boxes} коробок"]
]

# ================= OUTPUT =================

st.subheader("📊 Результаты проекта")

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.metric("Модули",f"{total_modules} шт")
    st.metric("Площадь",f"{area:.2f} м²")

with c2:
    st.metric("Разрешение",f"{res_w} × {res_h}")
    st.metric("Пикселей",f"{pixels:,}")

with c3:
    st.metric("Пиковая мощность",f"{peak_power/1000:.2f} кВт")
    st.metric("БП",f"{psu_count} шт")

with c4:
    st.metric("Карты",f"{cards} шт")
    st.metric("Порты",f"{ports} шт")

if port_load > 90:
    st.warning(f"Нагрузка порта {port_load:.1f}%")
else:
    st.success(f"Нагрузка порта {port_load:.1f}%")

st.info(f"Ток: {current:.1f} A | Автомат: {auto} | Кабель: {cable}")
st.info(f"Вес экрана: {total_weight:.1f} кг")
st.info(f"Упаковка: {boxes} коробок, {packing_weight} кг, {volume:.2f} м³")

# ================= BOM TABLE =================

st.subheader("📋 BOM ведомость")
st.table(bom)

# ================= NOVASTAR CONFIG JSON =================

config = {
    "resolution": f"{res_w}x{res_h}",
    "modules": total_modules,
    "cards": cards,
    "ports": ports,
    "processor": processor,
    "refresh": refresh,
    "pitch": pitch
}

st.subheader("⚙ Конфигурация Novastar (JSON)")
st.code(json.dumps(config, indent=4, ensure_ascii=False))

# ================= PDF =================

def generate_pdf():
    filename = f"LED_Project_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story=[]

    story.append(Paragraph("ИНЖЕНЕРНЫЙ ПРОЕКТ LED ЭКРАНА QIANGLI 320×160", styles["Title"]))
    story.append(Spacer(1,20))

    table = Table([["Позиция","Количество"]] + bom, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003366")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ]))

    story.append(table)
    doc.build(story)
    return filename

if st.button("📄 Сформировать инженерный PDF"):
    pdf = generate_pdf()
    with open(pdf,"rb") as f:
        st.download_button("⬇ Скачать PDF", f, file_name=pdf)
