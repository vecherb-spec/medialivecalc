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

# --- 1. БАЗЫ ДАННЫХ (ОПРЕДЕЛЯЕМ В САМОМ НАЧАЛЕ) ---

# Модули Qiangli
MODULES_DB = [
    {'name': 'Qiangli Q1.25 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 45.01},
    {'name': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 51.13},
    {'name': 'Qiangli R1.5 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 33.45},
    {'name': 'Qiangli Q1.53 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.43},
    {'name': 'VISTECH P1.53 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 42.4},
    {'name': 'Qiangli Q1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 500, 'max_power': 23.0, 'price_usd': 18.64},
    {'name': 'Qiangli Q2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 23.0, 'price_usd': 16.63},
    {'name': 'Qiangli Q2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.55},
    {'name': 'Qiangli Q3.07 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 500, 'max_power': 22.0, 'price_usd': 8.98},
    {'name': 'Qiangli Q4 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 7.56},
    {'name': 'Qiangli Q2.5 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.39},
    {'name': 'Qiangli Q3.07 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4200, 'max_power': 40.0, 'price_usd': 15.28},
    {'name': 'Qiangli Q4 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.02},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.09},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.62},
]

# Приемные карты (строки 10-19)
RECEIVING_CARDS_DB = [
    {"name": "Novastar MRV 208", "price_usd": 13.29, "type": "MRV"},
    {"name": "Novastar MRV 412", "price_usd": 15.40, "type": "MRV"},
    {"name": "Novastar MRV 416", "price_usd": 16.09, "type": "MRV"},
    {"name": "Novastar MRV 532", "price_usd": 21.00, "type": "MRV"},
    {"name": "Novastar CA50E (COEX)", "price_usd": 138.65, "type": "COEX"},
    {"name": "Novastar A5s Plus", "price_usd": 17.02, "type": "A"},
    {"name": "Novastar A7s Plus", "price_usd": 19.12, "type": "A"},
    {"name": "Novastar A8s", "price_usd": 33.89, "type": "A"},
    {"name": "Novastar A10s Plus", "price_usd": 44.57, "type": "A"},
    {"name": "Novastar A10s Pro", "price_usd": 71.31, "type": "A"},
]

# Блоки питания (строки 320-330)
PSU_DB = [
    {"name": "Mean Well LRS-200-5", "price_usd": 15.58},
    {"name": "Mean Well LRS-350-5", "price_usd": 21.05},
    {"name": "A-200JQ-5 slim", "price_usd": 13.57},
    {"name": "A-300FAR-4.5PH", "price_usd": 27.31},
    {"name": "A-400JQ-4.5PH", "price_usd": 17.69},
]

# Хабы (строки 127-129)
HUBS_DB = [
    {"name": "HUB 75Е", "price_usd": 5.29},
    {"name": "HUB 75Е-AXS (Серия A)", "price_usd": 14.86},
    {"name": "HUB 320-AXS (Серия A)", "price_usd": 14.86},
]

# Процессоры и порты
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Screen Pro Calculator | MediaLive", layout="wide", page_icon="🖥️")

# --- СТИЛИ ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #151a22 100%);
        border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center; border: 1px solid #2d3748; margin-bottom: 20px;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #63b3ed; }
    .metric-label { font-size: 13px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { background: linear-gradient(90deg, #3182ce, #2b6cb0); color: white; border-radius: 8px; width: 100%; }
    .section-header { color: #e2e8f0; font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #2d3748; }
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
        return 95.0
    except: return 95.0

# --- ИНИЦИАЛИЗАЦИЯ STATE ---
if "width_input" not in st.session_state: st.session_state.width_input = 3840
if "height_mm" not in st.session_state: st.session_state.height_mm = 2240

def fit_ratio(ratio):
    ideal = st.session_state.width_input / ratio
    st.session_state.height_mm = max(160, int(round(ideal / 160)) * 160)

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("📝 Проект")
project_name = st.sidebar.text_input("Имя проекта", value="MediaLive - Новый проект")
st.sidebar.markdown("---")
st.sidebar.header("💵 Финансы")
current_cbr_rate = get_cbr_usd_rate()
exchange_rate = st.sidebar.number_input("Курс USD (ЦБ + 1%)", value=float(current_cbr_rate), step=0.1)
price_per_m2 = st.sidebar.number_input("Цена за м² клиенту (₽)", value=150000, step=5000)

st.title("🖥️ Профессиональный калькулятор LED-экранов")

# БЛОК 1: РАЗМЕРЫ
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    width_mm = st.number_input("Ширина (мм) [Шаг 320]", min_value=320, step=320, key="width_input")
with c2:
    height_mm = st.number_input("Высота (мм) [Шаг 160]", min_value=160, step=160, value=st.session_state.height_mm)
    st.session_state.height_mm = height_mm

st.write("Быстрая подгонка:")
btn_cols = st.columns(4)
if btn_cols[0].button("16:9"): fit_ratio(1.777); st.rerun()
if btn_cols[1].button("4:3"): fit_ratio(1.333); st.rerun()
if btn_cols[2].button("21:9"): fit_ratio(2.333); st.rerun()
if btn_cols[3].button("1:1"): fit_ratio(1.0); st.rerun()

# БЛОК 2: МАТРИЦА
st.markdown('<div class="section-header">⚙️ 2. Светодиодные модули</div>', unsafe_allow_html=True)
ce, ct = st.columns(2)
env_key = ce.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
tech_options = sorted(list(set([m["tech"] for m in MODULES_DB if m["env"] == env_key])))
tech_key = ct.selectbox("Технология", tech_options)

available_mods = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
sel_mod_name = st.selectbox("Модель модуля:", [m["name"] for m in available_mods])
sel_mod = next(m for m in available_mods if m["name"] == sel_mod_name)

# БЛОК 3: УПРАВЛЕНИЕ И КАРТЫ
st.markdown('<div class="section-header">🎛️ 3. Система управления и Карты</div>', unsafe_allow_html=True)
cc1, cc2 = st.columns(2)
with cc1:
    processor = st.selectbox("Процессор / Контроллер", list(PROCESSOR_PORTS.keys()), index=12)
    m_per_card = st.number_input("Модулей на 1 карту:", value=12, min_value=1)
with cc2:
    sel_card_name = st.selectbox("Приёмная карта:", [c["name"] for c in RECEIVING_CARDS_DB], index=5)
    sel_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == sel_card_name)
    
    sel_hub_name, hub_price = "Встроенный", 0.0
    if sel_card["type"] == "A":
        sel_hub_name = st.selectbox("HUB для серии A:", [h["name"] for h in HUBS_DB], index=1)
        hub_price = next(h["price_usd"] for h in HUBS_DB if h["name"] == sel_hub_name)

# БЛОК 4: ПИТАНИЕ И ЗИП
st.markdown('<div class="section-header">⚡ 4. Питание и Резерв</div>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    sel_psu_name = st.selectbox("Модель БП (из прайса):", [p["name"] for p in PSU_DB], index=2)
    sel_psu = next(p for p in PSU_DB if p["name"] == sel_psu_name)
    m_per_psu = st.number_input("Модулей на 1 БП:", value=8, min_value=1)
with cp2:
    power_phase = st.radio("Вводная сеть", ["Одна фаза (220 В)", "Три фазы (380 В)"], horizontal=True)
    res_mod_per = st.slider("Резерв модулей (%)", 0, 10, 5)

# --- ИНЖЕНЕРНЫЕ РАСЧЕТЫ ---
mods_w, mods_h = width_mm // 320, height_mm // 160
total_mods = mods_w * mods_h
area_m2 = (width_mm * height_mm) / 1_000_000
total_mods_res = total_mods + math.ceil(total_mods * res_mod_per / 100)

n_cards = math.ceil(total_mods / m_per_card) + 1
n_psu = math.ceil(total_mods / m_per_psu) + 1
n_hubs = n_cards if sel_card["type"] == "A" else 0

peak_kw = (total_mods * sel_mod["max_power"]) / 1000
avg_kw = peak_kw * 0.35
voltage = 220 if "Одна фаза" in power_phase else 380 * 1.732
current = (peak_kw * 1200) / voltage
cable_sq = "1.5" if current < 15 else "2.5" if current < 21 else "4.0" if current < 27 else "6.0"

# Деньги
buy_usd = (total_mods_res * sel_mod["price_usd"]) + (n_cards * sel_card["price_usd"]) + (n_psu * sel_psu["price_usd"]) + (n_hubs * hub_price)
buy_rub = buy_usd * exchange_rate
sell_rub = area_m2 * price_per_m2

# --- ОТЧЕТ ---
st.markdown('<div class="section-header">📊 Финальный отчёт</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mods_w}x{mods_h}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Рабочая мощн.</div><div class="metric-value">{avg_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${buy_usd:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{buy_rub:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="metric-card"><div class="metric-label">Продажа (₽)</div><div class="metric-value">{sell_rub:,.0f}</div></div>', unsafe_allow_html=True)

with st.expander("📦 Детальная спецификация", expanded=True):
    st.write(f"- **Модули:** {total_mods} + {total_mods_res-total_mods} (ЗИП) = **{total_mods_res} шт.** (${total_mods_res*sel_mod['price_usd']:,.2f})")
    st.write(f"- **Приемные карты:** {sel_card['name']} — **{n_cards} шт.**")
    if n_hubs > 0: st.write(f"- **Хабы Серии A:** {sel_hub_name} — **{n_hubs} шт.**")
    st.write(f"- **Блоки питания:** {sel_psu['name']} — **{n_psu} шт.**")
    st.write(f"- **Конструктив:** Магниты — {total_mods*4} шт, Профиль верт. — {mods_w+1} шт")
    st.write(f"- **Электрика:** Кабель 3х{cable_sq} мм², Ток пиковый — {current:.1f} А")

# Схема
st.subheader("📐 Схема расположения модулей")
html_grid = f'<div style="display: grid; grid-template-columns: repeat({mods_w}, 1fr); gap: 2px; background:#2d3748; padding:4px; max-width:800px; margin:auto;">'
for _ in range(total_mods): html_grid += '<div style="background:#48bb78; aspect-ratio:2/1;"></div>'
st.components.v1.html(html_grid + "</div>", height=int(800*(mods_h/mods_w))+40)

# Экспорт
st.markdown('<div class="section-header">🔗 Экспорт</div>', unsafe_allow_html=True)
st.code(json.dumps({"project": project_name, "dims": f"{width_mm}x{height_mm}", "buy_rub": round(buy_rub), "sell_rub": round(sell_rub)}, indent=2, ensure_ascii=False), language="json")
