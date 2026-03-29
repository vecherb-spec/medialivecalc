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
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #2d3748;
        margin-bottom: 20px;
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

# --- БАЗЫ ДАННЫХ ---
MODULES_DB = [
    # INDOOR
    {'name': 'Qiangli Q1.25 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 45.01},
    {'name': 'Qiangli Q1.25 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 46.13},
    {'name': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 51.13},
    {'name': 'Qiangli R1.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 33.45},
    {'name': 'Qiangli Q1.53 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.43},
    {'name': 'VISTECH P1.53 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 42.4},
    {'name': 'Qiangli Q1.53 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 30.43},
    {'name': 'Qiangli Q1.53 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 35.16},
    {'name': 'Qiangli Q1.66 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.66, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 26.49},
    {'name': 'Qiangli Q1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 500, 'max_power': 23.0, 'price_usd': 18.64},
    {'name': 'Qiangli R1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 21.99},
    {'name': 'VISTECH P1.86 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.75},
    {'name': 'Qiangli Q1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 20.0},
    {'name': 'Qiangli R1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 22.88},
    {'name': 'Qiangli Q2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 23.0, 'price_usd': 16.63},
    {'name': 'Qiangli R2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 19.97},
    {'name': 'Qiangli Q2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 23.0, 'price_usd': 17.6},
    {'name': 'Qiangli R2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 20.78},
    {'name': 'Qiangli Q2 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'GOB', 'brightness': 600, 'max_power': 23.0, 'price_usd': 21.84},
    {'name': 'Qiangli Q2.5 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.03},
    {'name': 'Qiangli Q2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.55},
    {'name': 'Qiangli R2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 24.0, 'price_usd': 14.87},
    {'name': 'Qiangli Q2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 500, 'max_power': 24.0, 'price_usd': 13.42},
    {'name': 'Qiangli R2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 600, 'max_power': 24.0, 'price_usd': 15.56},
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
    {'name': 'Qiangli R4 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'Flexible', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 25.08},
    {'name': 'Qiangli Q4 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.48},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.09},
    {'name': 'Qiangli Q5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.54},
    {'name': 'Qiangli Q6.66 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 4500, 'max_power': 46.0, 'price_usd': 8.86},
    {'name': 'Qiangli Q6.66 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 9.28},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.62},
    {'name': 'Qiangli Q8 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 8.04},
]

CARDS_DB = [
    {"name": "MRV 208-1 / MRV 208-N", "price_usd": 10.66, "type": "MRV"},
    {"name": "MRV 412", "price_usd": 15.17, "type": "MRV"},
    {"name": "MRV 416", "price_usd": 15.57, "type": "MRV"},
    {"name": "MRV 432", "price_usd": 15.98, "type": "MRV"},
    {"name": "MRV 532", "price_usd": 18.03, "type": "MRV"},
    {"name": "A4s Plus", "price_usd": 17.63, "type": "A-Series"},
    {"name": "A5s Plus", "price_usd": 19.68, "type": "A-Series"},
    {"name": "A7s Plus", "price_usd": 31.57, "type": "A-Series"},
    {"name": "A8s / A8s-N", "price_usd": 51.25, "type": "A-Series"},
    {"name": "A10s Plus-N", "price_usd": 72.56, "type": "A-Series"},
]

CONTROLLERS_DB = {
    "Синхронные": [
        {"name": "Novastar MSD 300", "price_usd": 100.63, "desc": "1,3 млн пикс"},
        {"name": "Novastar MSD 600", "price_usd": 207.03, "desc": "2,3 млн пикс"},
        {"name": "Novastar MCTRL 300", "price_usd": 155.53, "desc": "1,3 млн пикс"},
        {"name": "Novastar MCTRL 600", "price_usd": 278.31, "desc": "2,3 млн пикс"},
        {"name": "Novastar MCTRL 700", "price_usd": 290.46, "desc": "2,3 млн пикс, 6 выходов"},
        {"name": "Novastar MX30", "price_usd": 2228.28, "desc": "COEX, 6.5 млн пикс"},
    ],
    "Асинхронные": [
        {"name": "TB10 Plus", "price_usd": 58.61, "desc": "650к пикс"},
        {"name": "TB30", "price_usd": 236.39, "desc": "650к пикс"},
        {"name": "TB40", "price_usd": 181.28, "desc": "1,3 млн пикс"},
        {"name": "TB60", "price_usd": 404.58, "desc": "2,6 млн пикс"},
    ]
}

PROCESSORS_DB = [
    {"name": "VX400S-N", "price_usd": 490.28},
    {"name": "VX600", "price_usd": 987.77},
    {"name": "VX1000", "price_usd": 1357.54},
    {"name": "VC4", "price_usd": 179.22},
    {"name": "VC10", "price_usd": 889.92},
]

PSU_DB = [
    {"name": "Mean Well LRS-200-5", "price_usd": 15.58},
    {"name": "A-200JQ-5 slim", "price_usd": 13.57},
    {"name": "A-400JQ-4.5PH", "price_usd": 17.69},
]

HUB_PRICE_USD = 4.10

# --- ИНИЦИАЛИЗАЦИЯ ---
if "width_input" not in st.session_state: st.session_state.width_input = 3840
if "height_mm" not in st.session_state: st.session_state.height_mm = 2240

# --- UI ---
st.sidebar.header("💵 Финансы")
rate = get_cbr_usd_rate()
exchange_rate = st.sidebar.number_input("Курс USD (ЦБ+1%)", value=rate)
price_per_m2 = st.sidebar.number_input("Цена клиенту за м² (₽)", value=150000)

st.title("🖥️ Калькулятор LED MediaLive")

# БЛОК 1
st.markdown('<div class="section-header">📏 1. Размеры</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
width_mm = c1.number_input("Ширина (мм)", min_value=320, step=320, key="width_input")
height_mm = c2.number_input("Высота (мм)", min_value=160, step=160, value=st.session_state.height_mm)
st.session_state.height_mm = height_mm

# БЛОК 2
st.markdown('<div class="section-header">⚙️ 2. Модули</div>', unsafe_allow_html=True)
ce, ct = st.columns(2)
env_key = ce.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
tech_options = sorted(list(set([m["tech"] for m in MODULES_DB if m["env"] == env_key])))
tech_key = ct.selectbox("Технология", tech_options)
available_modules = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
sel_mod = next(m for m in available_modules if m["name"] == st.selectbox("Выберите модель:", [m["name"] for m in available_modules]))

# БЛОК 3
st.markdown('<div class="section-header">🎛️ 3. Управление</div>', unsafe_allow_html=True)
ct1, ct2 = st.columns(2)
sys_type = ct1.radio("Тип системы", ["Процессор", "Контроллер"], horizontal=True)
if sys_type == "Контроллер":
    sub = ct2.selectbox("Категория", list(CONTROLLERS_DB.keys()))
    sel_sys = next(c for c in CONTROLLERS_DB[sub] if c["name"] == st.selectbox("Модель:", [x["name"] for x in CONTROLLERS_DB[sub]]))
else:
    sel_sys = next(p for p in PROCESSORS_DB if p["name"] == st.selectbox("Модель:", [x["name"] for x in PROCESSORS_DB]))

# БЛОК 4
st.markdown('<div class="section-header">⚡ 4. Карты и Питание</div>', unsafe_allow_html=True)
cc, cp = st.columns(2)
with cc:
    sel_card = next(c for c in CARDS_DB if c["name"] == st.selectbox("Приемная карта:", [c["name"] for c in CARDS_DB], index=6))
    m_per_c = st.number_input("Модулей на карту:", value=12)
with cp:
    sel_psu = next(p for p in PSU_DB if p["name"] == st.selectbox("Блок питания:", [p["name"] for p in PSU_DB]))
    m_per_p = st.number_input("Модулей на БП:", value=8)

# РАСЧЕТЫ
total_mods = (width_mm // 320) * (height_mm // 160)
res_mod = math.ceil(total_mods * 0.05)
num_cards = math.ceil(total_mods / m_per_c) + 1
num_psu = math.ceil(total_mods / m_per_p) + 1
needs_hub = sel_card["type"] == "A-Series"
num_hubs = num_cards if needs_hub else 0

# ДЕНЬГИ
c_mod = (total_mods + res_mod) * sel_mod["price_usd"]
c_card = num_cards * sel_card["price_usd"]
c_psu = num_psu * sel_psu["price_usd"]
c_sys = sel_sys["price_usd"]
c_hub = num_hubs * HUB_PRICE_USD
total_usd = c_mod + c_card + c_psu + c_sys + c_hub
total_rub = total_usd * exchange_rate

# ИТОГИ
st.markdown('<div class="section-header">📊 Смета</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{width_mm//320}x{height_mm//160}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Модулей</div><div class="metric-value">{total_mods}+{res_mod} шт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${total_usd:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{total_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)

with st.expander("Детализация закупки"):
    st.write(f"- Модули: {total_mods+res_mod} шт x ${sel_mod['price_usd']}")
    st.write(f"- Управление: {sel_sys['name']} (${sel_sys['price_usd']})")
    st.write(f"- Карты: {num_cards} шт x ${sel_card['price_usd']}")
    if needs_hub: st.write(f"- Хабы: {num_hubs} шт x ${HUB_PRICE_USD}")
    st.write(f"- БП: {num_psu} шт x ${sel_psu['price_usd']}")
