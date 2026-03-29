import streamlit as st
import math
import json
import datetime
import urllib.request
import xml.etree.ElementTree as ET

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Pro Calc | MediaLive", layout="wide", page_icon="🖥️")

# --- СОВРЕМЕННЫЙ CSS ДИЗАЙН ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #151a22 100%);
        border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #2d3748; margin-bottom: 20px;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #63b3ed; }
    .metric-label { font-size: 13px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button {
        background: linear-gradient(90deg, #3182ce, #2b6cb0); 
        color: white; border: none; border-radius: 8px; transition: all 0.3s; width: 100%;
    }
    .section-header {
        color: #e2e8f0; font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem;
        margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #2d3748;
    }
    div[data-testid="stExpander"] { background-color: #1a202c; border-radius: 8px; border: 1px solid #2d3748; }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ---
@st.cache_data(ttl=3600)
def get_cbr_usd_rate():
    try:
        url = "http://www.cbr.ru/scripts/XML_daily.asp"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for valute in root.findall('Valute'):
            if valute.attrib.get('ID') == 'R01235':
                return round(float(valute.find('Value').text.replace(',', '.')) * 1.01, 2)
        return 100.0
    except: return 100.0

# --- БАЗЫ ДАННЫХ (ИЗ ТВОЕГО ПРАЙСА) ---
MODULES_DB = [
    # INDOOR
    {'name': 'Qiangli Q1.25 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 45.01},
    {'name': 'Qiangli Q1.25 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 46.13},
    {'name': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 51.13},
    {'name': 'Qiangli R1.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.5, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 23.0, 'price_usd': 33.45},
    {'name': 'Qiangli Q1.53 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.43},
    {'name': 'VISTECH P1.53 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 42.4},
    {'name': 'Qiangli Q1.53 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 30.43},
    {'name': 'Qiangli Q1.53 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 35.16},
    {'name': 'Qiangli Q1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 500, 'max_power': 23.0, 'price_usd': 18.64},
    {'name': 'Qiangli R1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 23.0, 'price_usd': 21.99},
    {'name': 'VISTECH P1.86 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.75},
    {'name': 'Qiangli Q1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 20.0},
    {'name': 'Qiangli R1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 23.0, 'price_usd': 22.88},
    {'name': 'Qiangli Q2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 23.0, 'price_usd': 16.63},
    {'name': 'Qiangli R2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 23.0, 'price_usd': 19.97},
    {'name': 'Qiangli Q2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 23.0, 'price_usd': 17.6},
    {'name': 'Qiangli R2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 23.0, 'price_usd': 20.78},
    {'name': 'Qiangli Q2 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'GOB', 'brightness': 600, 'max_power': 23.0, 'price_usd': 21.84},
    {'name': 'Qiangli Q2.5 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.03},
    {'name': 'Qiangli Q2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.55},
    {'name': 'Qiangli R2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Гибкий', 'brightness': 500, 'max_power': 24.0, 'price_usd': 14.87},
    {'name': 'Qiangli Q2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 500, 'max_power': 24.0, 'price_usd': 13.42},
    {'name': 'Qiangli R2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Гибкий', 'brightness': 600, 'max_power': 24.0, 'price_usd': 15.56},
    {'name': 'Qiangli Q3.07 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 500, 'max_power': 22.0, 'price_usd': 8.98},
    {'name': 'Qiangli Q3.07 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 600, 'max_power': 22.0, 'price_usd': 10.61},
    {'name': 'Qiangli Q3.07 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 600, 'max_power': 22.0, 'price_usd': 10.99},
    {'name': 'Qiangli Q4 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 7.56},
    {'name': 'Qiangli Q4 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 24.0, 'price_usd': 8.46},
    {'name': 'Qiangli Q4 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 24.0, 'price_usd': 8.66},
    # OUTDOOR
    {'name': 'Qiangli Q2.5 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.39},
    {'name': 'Qiangli Q2.5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.8},
    {'name': 'Qiangli Q3.07 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4200, 'max_power': 40.0, 'price_usd': 15.28},
    {'name': 'Qiangli Q3.07 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4500, 'max_power': 40.0, 'price_usd': 16.11},
    {'name': 'Qiangli Q4 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.02},
    {'name': 'Qiangli R4 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'Гибкий', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 25.08},
    {'name': 'Qiangli Q4 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.48},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.09},
    {'name': 'Qiangli Q5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.54},
    {'name': 'Qiangli Q6.66 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 4500, 'max_power': 46.0, 'price_usd': 8.86},
    {'name': 'Qiangli Q6.66 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 9.28},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.62},
    {'name': 'Qiangli Q8 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 8.04},
]

CARDS_DB = [
    {"name": "MRV 208-1 / MRV 208-N", "price": 10.66, "type": "MRV"},
    {"name": "MRV 412", "price": 15.17, "type": "MRV"},
    {"name": "MRV 416", "price": 15.57, "type": "MRV"},
    {"name": "A4s Plus", "price": 17.63, "type": "A"},
    {"name": "A5s Plus", "price": 19.68, "type": "A"},
    {"name": "A7s Plus", "price": 31.57, "type": "A"},
    {"name": "A8s / A8s-N", "price": 51.25, "type": "A"},
    {"name": "A10s Plus-N", "price": 72.56, "type": "A"},
]

SYS_DB = {
    "Видеопроцессор": [
        {"name": "VX400", "price": 889.92}, {"name": "VX600", "price": 987.77},
        {"name": "VX1000", "price": 1357.54}, {"name": "VC4", "price": 179.22},
        {"name": "VC10", "price": 889.92}, {"name": "NovaPro UHD", "price": 3090.00}
    ],
    "Контроллер (Синхрон)": [
        {"name": "MSD 300", "price": 100.63}, {"name": "MSD 600", "price": 207.03},
        {"name": "MCTRL 300", "price": 155.53}, {"name": "MCTRL 600", "price": 278.31},
        {"name": "MCTRL 700", "price": 290.46}, {"name": "MX30", "price": 2228.28}
    ],
    "Контроллер (Асинхрон)": [
        {"name": "TB10 Plus", "price": 58.61}, {"name": "TB30", "price": 236.39},
        {"name": "TB40", "price": 181.28}, {"name": "TB60", "price": 404.58}
    ]
}

PSU_DB = [
    {"name": "Mean Well LRS-200-5", "price": 15.58},
    {"name": "A-200JQ-5 slim", "price": 13.57},
    {"name": "A-400JQ-4.5PH", "price": 17.69},
]

# --- ИНИЦИАЛИЗАЦИЯ ---
if "w_in" not in st.session_state: st.session_state.w_in = 3840
if "h_in" not in st.session_state: st.session_state.h_in = 2240

def set_size(r):
    st.session_state.h_in = max(160, int(round((st.session_state.w_in / r) / 160)) * 160)

# --- UI ---
st.sidebar.header("💵 Финансы")
ex_rate = st.sidebar.number_input("Курс USD (ЦБ+1%)", value=get_cbr_usd_rate())
price_per_m2 = st.sidebar.number_input("Цена продажи/м² (₽)", value=150000)

st.title("🖥️ LED MediaLive Pro Calculator")

# БЛОК 1: РАЗМЕРЫ
st.markdown('<div class="section-header">📏 1. Геометрия и Размеры</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
w_mm = c1.number_input("Ширина экрана (мм) [Шаг 320]", min_value=320, step=320, key="w_in")
h_mm = c2.number_input("Высота экрана (мм) [Шаг 160]", min_value=160, step=160, value=st.session_state.h_in)
st.session_state.h_in = h_mm

st.write("Быстрая подгонка:")
b1, b2, b3, b4 = st.columns(4)
if b1.button("16:9"): set_size(1.777); st.rerun()
if b2.button("4:3"): set_size(1.333); st.rerun()
if b3.button("21:9"): set_size(2.333); st.rerun()
if b4.button("1:1"): set_size(1.0); st.rerun()

# БЛОК 2: МОДУЛИ
st.markdown('<div class="section-header">⚙️ 2. Характеристики модулей</div>', unsafe_allow_html=True)
ce, ct = st.columns(2)
env = ce.radio("Среда использования", ["Indoor", "Outdoor"], horizontal=True)
techs = sorted(list(set(m["tech"] for m in MODULES_DB if m["env"] == env)))
tech = ct.selectbox("Технология исполнения", techs)
mods = [m for m in MODULES_DB if m["env"] == env and m["tech"] == tech]
sel_mod = next(m for m in mods if m["name"] == st.selectbox("Модель модуля Qiangli:", [x["name"] for x in mods]))

# БЛОК 3: КОМПЛЕКТУЮЩИЕ
st.markdown('<div class="section-header">🎛️ 3. Управление и Питание</div>', unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns(3)
with cc1:
    cat = st.selectbox("Тип управления:", list(SYS_DB.keys()))
    sel_sys = next(s for s in SYS_DB[cat] if s["name"] == st.selectbox("Модель устройства:", [x["name"] for x in SYS_DB[cat]]))
with cc2:
    sel_card = next(c for c in CARDS_DB if c["name"] == st.selectbox("Приемная карта:", [x["name"] for x in CARDS_DB], index=4))
    m_card = st.number_input("Модулей на карту:", value=12)
with cc3:
    sel_psu = next(p for p in PSU_DB if p["name"] == st.selectbox("Модель БП:", [x["name"] for x in PSU_DB]))
    m_psu = st.number_input("Модулей на БП:", value=8)

# --- РАСЧЕТЫ ---
t_mod = (w_mm // 320) * (h_mm // 160)
mods_w = w_mm // 320
mods_h = h_mm // 160
r_mod = math.ceil(t_mod * 0.05)
n_card = math.ceil(t_mod / m_card) + 1
n_psu = math.ceil(t_mod / m_psu) + 1
needs_hub = sel_card["type"] == "A"
n_hub = n_card if needs_hub else 0

# Электрика
peak_kw = t_mod * sel_mod["max_power"] / 1000
avg_kw = peak_kw * 0.35
current = (peak_kw * 1200) / 220 # с запасом
sq = "1.5" if current < 15 else "2.5" if current < 21 else "4.0" if current < 27 else "6.0"

# Деньги
c_mod = (t_mod + r_mod) * sel_mod["price_usd"]
c_card = n_card * sel_card["price"]
c_psu = n_psu * sel_psu["price"]
c_sys = sel_sys["price"]
c_hub = n_hub * 4.10
total_usd = c_mod + c_card + c_psu + c_sys + c_hub
total_rub = total_usd * ex_rate
sell_price = (w_mm * h_mm / 1_000_000) * price_per_m2

# --- ИТОГИ ---
st.markdown('<div class="section-header">📊 Финальный отчёт</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mods_w}x{mods_h}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Мощность (Раб)</div><div class="metric-value">{avg_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${total_usd:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{total_rub:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="metric-card"><div class="metric-label">Продажа (₽)</div><div class="metric-value">{sell_price:,.0f}</div></div>', unsafe_allow_html=True)

with st.expander("📦 Спецификация модулей и ЗИП", expanded=True):
    st.write(f"- **Модель:** {sel_mod['name']} (P{sel_mod['pitch']})")
    st.write(f"- **Количество:** {t_mod} шт + {r_mod} шт (ЗИП) = **{t_mod+r_mod} шт.**")
    st.write(f"- **Стоимость:** ${c_mod:,.2f}")

with st.expander("🔌 Электроника и Питание"):
    st.write(f"- **Блок питания:** {sel_psu['name']} — **{n_psu} шт.**")
    st.write(f"- **Приемные карты:** {sel_card['name']} — **{n_card} шт.**")
    if needs_hub: st.write(f"- **Хабы HUB75E-001:** **{n_hub} шт.**")
    st.write(f"- **Система:** {sel_sys['name']} — 1 шт.")

with st.expander("🏗️ Конструктив и Сеть"):
    vert = mods_w + 1
    st.write(f"- **Магниты:** {t_mod * 4} шт.")
    st.write(f"- **Вертикальный профиль:** {vert} шт. по {h_mm-40} мм")
    st.write(f"- **Кабель ВВГ:** {sq} мм² (Ток: {current:.1f} А)")

# Figma Экспорт
st.markdown('<div class="section-header">🔗 Экспорт данных</div>', unsafe_allow_html=True)
figma = {
    "project": project_name, "date": str(datetime.date.today()),
    "dims": f"{w_mm}x{h_mm}", "res": f"{int(w_mm/sel_mod['pitch'])}x{int(h_mm/sel_mod['pitch'])}",
    "buy_rub": round(total_rub), "sell_rub": round(sell_price), "margin": round(sell_price - total_rub)
}
st.code(json.dumps(figma, indent=2, ensure_ascii=False), language="json")

# СХЕМА
st.subheader("📐 Схема сборки (Вид спереди)")
html_grid = f'<div style="display: grid; grid-template-columns: repeat({mods_w}, 1fr); gap: 2px; background:#2d3748; padding:5px; max-width:800px; margin:auto;">'
for _ in range(t_mod): html_grid += '<div style="background:#48bb78; aspect-ratio:2/1; border-radius:2px;"></div>'
html_grid += "</div>"
st.components.v1.html(html_grid, height=int(800 * (mods_h/mods_w)) + 50)
