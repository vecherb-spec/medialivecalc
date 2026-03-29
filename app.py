import streamlit as st
import math
import json
import datetime
import urllib.request
import xml.etree.ElementTree as ET

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    pass

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Screen Pro Calculator | MediaLive", layout="wide", page_icon="🖥️")

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
                return float(valute.find('Value').text.replace(',', '.')) * 1.01
        return 95.0
    except: return 95.0

# --- БАЗЫ ДАННЫХ (ИЗ ПРАЙСА) ---
MODULES_DB = [
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

RECEIVING_CARDS_DB = [
    {"name": "MRV 208-1 / MRV 208-N", "max_px": 256*256, "price_usd": 10.66, "type": "MRV"},
    {"name": "MRV 412", "max_px": 512*512, "price_usd": 15.17, "type": "MRV"},
    {"name": "MRV 416", "max_px": 512*384, "price_usd": 15.57, "type": "MRV"},
    {"name": "MRV 432", "max_px": 512*512, "price_usd": 15.98, "type": "MRV"},
    {"name": "MRV 532", "max_px": 512*512, "price_usd": 18.03, "type": "MRV"},
    {"name": "A4s Plus", "max_px": 256*256, "price_usd": 17.63, "type": "A-Series"},
    {"name": "A5s Plus", "max_px": 320*256, "price_usd": 19.68, "type": "A-Series"},
    {"name": "A7s Plus", "max_px": 512*256, "price_usd": 31.57, "type": "A-Series"},
    {"name": "A8s / A8s-N", "max_px": 512*384, "price_usd": 51.25, "type": "A-Series"},
    {"name": "A10s Plus-N", "max_px": 512*512, "price_usd": 72.56, "type": "A-Series"},
]

HUB_PRICE_USD = 4.10  # Хаб HUB75E-001 (строка 128)

# --- ИНИЦИАЛИЗАЦИЯ ---
if "width_input" not in st.session_state: st.session_state.width_input = 3840
if "height_mm" not in st.session_state: st.session_state.height_mm = 2240

def fit_ratio(ratio):
    ideal = st.session_state.width_input / ratio
    st.session_state.height_mm = max(160, int(round(ideal / 160)) * 160)

# --- КУРС ---
exchange_rate = st.sidebar.number_input("Курс USD (ЦБ+1%)", value=get_cbr_usd_rate(), step=0.1)

# ==========================================
# БЛОК 1: ГЕОМЕТРИЯ
# ==========================================
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: width_mm = st.number_input("Ширина (мм)", min_value=320, step=320, key="width_input")
with c2: height_mm = st.number_input("Высота (мм)", min_value=160, step=160, value=st.session_state.height_mm)
st.session_state.height_mm = height_mm

st.write("Подгонка:")
b1, b2, b3, b4 = st.columns(4)
if b1.button("16:9"): fit_ratio(1.777); st.rerun()
if b2.button("4:3"): fit_ratio(1.333); st.rerun()
if b3.button("21:9"): fit_ratio(2.333); st.rerun()
if b4.button("1:1"): fit_ratio(1.0); st.rerun()

# ==========================================
# БЛОК 2: МОДУЛИ
# ==========================================
st.markdown('<div class="section-header">⚙️ 2. Светодиодные модули</div>', unsafe_allow_html=True)
c_env, c_tech = st.columns(2)
env_key = c_env.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
tech_options = sorted(list(set([m["tech"] for m in MODULES_DB if m["env"] == env_key])))
tech_key = c_tech.selectbox("Технология", tech_options)

available_modules = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
selected_mod_name = st.selectbox("Выберите модуль:", [m["name"] for m in available_modules])
sel_mod = next(m for m in available_modules if m["name"] == selected_mod_name)

# ==========================================
# БЛОК 3: УПРАВЛЕНИЕ
# ==========================================
st.markdown('<div class="section-header">🎛️ 3. Приемные карты</div>', unsafe_allow_html=True)
c_card, c_sc = st.columns(2)
with c_card:
    sel_card_name = st.selectbox("Модель приемной карты:", [c["name"] for c in RECEIVING_CARDS_DB], index=1)
    sel_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == sel_card_name)
with c_sc:
    mod_per_card = st.selectbox("Модулей на карту:", [8, 10, 12, 16, 20], index=2)

# Авто-логика хабов
needs_hub = sel_card["type"] == "A-Series"
hub_text = f"Требуется хаб HUB75E (закупка: ${HUB_PRICE_USD})" if needs_hub else "Хаб не требуется (встроен в карту)"
st.info(f"ℹ️ {hub_text}")

# ==========================================
# РАСЧЕТЫ
# ==========================================
mods_w = width_mm // 320
mods_h = height_mm // 160
total_mods = mods_w * mods_h
area = (width_mm * height_mm) / 1_000_000

# Резерв
res_mod = math.ceil(total_mods * 0.05)
total_mods_order = total_mods + res_mod

# Карты и Хабы
num_cards = math.ceil(total_mods / mod_per_card)
num_cards_res = num_cards + 1
num_hubs = num_cards_res if needs_hub else 0

# Деньги (ЗАКУПКА)
cost_mod = total_mods_order * sel_mod["price_usd"]
cost_card = num_cards_res * sel_card["price_usd"]
cost_hub = num_hubs * HUB_PRICE_USD
total_purchase_usd = cost_mod + cost_card + cost_hub
total_purchase_rub = total_purchase_usd * exchange_rate

# ==========================================
# ОТЧЕТ
# ==========================================
st.markdown('<div class="section-header">📊 Результаты расчета</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Разрешение</div><div class="metric-value">{int(width_mm/sel_mod["pitch"])}x{int(height_mm/sel_mod["pitch"])}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Модулей</div><div class="metric-value">{total_mods} + {res_mod} шт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Карт / Хабов</div><div class="metric-value">{num_cards_res} / {num_hubs} шт</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><div class="metric-label">Электроника (Закупка)</div><div class="metric-value">{total_purchase_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)

with st.expander("Детальная спецификация электроники"):
    st.write(f"- **Модули ({sel_mod['name']}):** {total_mods_order} шт. x ${sel_mod['price_usd']} = ${cost_mod:,.2f}")
    st.write(f"- **Карты ({sel_card['name']}):** {num_cards_res} шт. x ${sel_card['price_usd']} = ${cost_card:,.2f}")
    if needs_hub:
        st.write(f"- **Хабы (HUB75E-001):** {num_hubs} шт. x ${HUB_PRICE_USD} = ${cost_hub:,.2f}")
    st.write(f"---")
    st.write(f"**Итого закупка электроники:** ${total_purchase_usd:,.2f} (**{total_purchase_rub:,.0f} ₽** по курсу {exchange_rate})")
