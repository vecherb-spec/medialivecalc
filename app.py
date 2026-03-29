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
        color: white; 
        border: none; 
        border-radius: 8px; 
        transition: all 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px); 
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }
    .section-header {
        color: #e2e8f0;
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2d3748;
    }
    div[data-testid="stExpander"] {
        background-color: #1a202c;
        border-radius: 8px;
        border: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИЯ ПАРСИНГА КУРСА ЦБ РФ (+1%) ---
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
    except Exception:
        return 95.0

# --- БАЗЫ ДАННЫХ (ОБНОВЛЕНО ПО ПРАЙСУ) ---
MODULES_DB = [
    # INDOOR
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
    # OUTDOOR
    {'name': 'Qiangli Q2.5 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.39},
    {'name': 'Qiangli Q3.07 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4200, 'max_power': 40.0, 'price_usd': 15.28},
    {'name': 'Qiangli Q4 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.02},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.09},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.62},
]

RECEIVING_CARDS_DB = [
    {"name": "MRV 208-1 / MRV 208-N", "price_usd": 10.66, "type": "MRV"},
    {"name": "MRV 412", "price_usd": 15.17, "type": "MRV"},
    {"name": "MRV 416", "price_usd": 15.57, "type": "MRV"},
    {"name": "A4s Plus", "price_usd": 17.63, "type": "A"},
    {"name": "A5s Plus", "price_usd": 19.68, "type": "A"},
    {"name": "A7s Plus", "price_usd": 31.57, "type": "A"},
    {"name": "A8s / A8s-N", "price_usd": 51.25, "type": "A"},
    {"name": "A10s Plus-N", "price_usd": 72.56, "type": "A"},
]

PSU_DB = [
    {"name": "Mean Well LRS-200-5", "price_usd": 15.58, "max_w": 200},
    {"name": "Mean Well LRS-350-5", "price_usd": 21.05, "max_w": 350},
    {"name": "A-200JQ-5 slim", "price_usd": 13.57, "max_w": 200},
    {"name": "A-300FAR-4.5PH", "price_usd": 27.31, "max_w": 300},
    {"name": "A-400JQ-4.5PH", "price_usd": 17.69, "max_w": 400},
]

HUB_PRICE_USD = 4.10 # HUB75E-001 (строка 128)

# --- ИНИЦИАЛИЗАЦИЯ STATE ---
if "width_input" not in st.session_state: st.session_state.width_input = 3840
if "height_mm" not in st.session_state: st.session_state.height_mm = 2240

def fit_ratio(ratio):
    ideal = st.session_state.width_input / ratio
    st.session_state.height_mm = max(160, int(round(ideal / 160)) * 160)

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("📝 Данные проекта")
project_name = st.sidebar.text_input("Имя проекта", value="MediaLive Project")
client_name = st.sidebar.text_input("Клиент", placeholder="Имя заказчика")

st.sidebar.markdown("---")
st.sidebar.header("💵 Финансы")
current_rate = get_cbr_usd_rate()
exchange_rate = st.sidebar.number_input("Курс USD (ЦБ + 1%)", value=current_rate, step=0.1)
price_per_m2 = st.sidebar.number_input("Цена продажи за м² (₽)", value=150000, step=5000)

st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Расчет комплектующих на базе динамического прайс-листа.")

# ==========================================
# БЛОК 1: ГЕОМЕТРИЯ
# ==========================================
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)

col_w, col_h = st.columns(2)
with col_w:
    width_mm = st.number_input("Ширина экрана (мм) [Шаг 320]", min_value=320, step=320, key="width_input")
with col_h:
    height_mm = st.number_input("Высота экрана (мм) [Шаг 160]", min_value=160, step=160, value=st.session_state.height_mm)
    st.session_state.height_mm = height_mm

st.write("Быстрая подгонка:")
b1, b2, b3, b4 = st.columns(4)
if b1.button("16:9"): fit_ratio(1.777); st.rerun()
if b2.button("4:3"): fit_ratio(1.333); st.rerun()
if b3.button("21:9"): fit_ratio(2.333); st.rerun()
if b4.button("1:1"): fit_ratio(1.0); st.rerun()

# ==========================================
# БЛОК 2: МАТРИЦА
# ==========================================
st.markdown('<div class="section-header">⚙️ 2. Светодиодные модули</div>', unsafe_allow_html=True)

c_env, c_tech = st.columns(2)
env_key = c_env.radio("Среда использования", ["Indoor", "Outdoor"], horizontal=True)
tech_options = sorted(list(set([m["tech"] for m in MODULES_DB if m["env"] == env_key])))
tech_key = c_tech.selectbox("Технология", tech_options)

available_modules = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
selected_module_name = st.selectbox("Выберите модуль из прайса:", [m["name"] for m in available_modules])
sel_mod = next(m for m in available_modules if m["name"] == selected_module_name)

# ==========================================
# БЛОК 3: ЭЛЕКТРОНИКА
# ==========================================
st.markdown('<div class="section-header">🎛️ 3. Управление и Питание</div>', unsafe_allow_html=True)

cc1, cc2, cc3 = st.columns(3)
with cc1:
    processor = st.selectbox("Процессор / Контроллер", ["VX400", "VX600", "VX1000", "VC4", "VC10", "MSD300", "TB30", "TB60"])
    power_phase = st.radio("Вводная сеть", ["Одна фаза (220 В)", "Три фазы (380 В)"], horizontal=True)

with cc2:
    sel_card_name = st.selectbox("Приёмная карта:", [c["name"] for c in RECEIVING_CARDS_DB], index=4)
    sel_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == sel_card_name)
    m_per_c = st.number_input("Модулей на 1 карту:", value=12, min_value=1)

with cc3:
    sel_psu_name = st.selectbox("Блок питания:", [p["name"] for p in PSU_DB], index=2)
    sel_psu = next(p for p in PSU_DB if p["name"] == sel_psu_name)
    m_per_p = st.number_input("Модулей на 1 БП:", value=8, min_value=1)

# ==========================================
# РАСЧЕТЫ (ИНЖЕНЕРИЯ + ФИНАНСЫ)
# ==========================================
mods_w = width_mm // 320
mods_h = height_mm // 160
total_mods = mods_w * mods_h
area_m2 = (width_mm * height_mm) / 1_000_000

# Резерв и заказ
res_mod = math.ceil(total_mods * 0.05)
total_mods_order = total_mods + res_mod

# Карты, БП, Хабы
n_cards = math.ceil(total_mods / m_per_c) + 1
n_psu = math.ceil(total_mods / m_per_p) + 1
needs_hub = sel_card["type"] == "A"
n_hubs = n_cards if needs_hub else 0

# Мощность и Электрика
peak_power_kw = total_mods * sel_mod["max_power"] / 1000
avg_power_kw = peak_power_kw * 0.35
voltage = 220 if "Одна фаза" in power_phase else 380 * 1.732
current = (peak_power_kw * 1200) / voltage # +20% запас
cable_sq = "1.5" if current < 15 else "2.5" if current < 21 else "4.0" if current < 27 else "6.0"
breaker = 16 if current < 13 else 25 if current < 20 else 32 if current < 26 else 40

# Финансы
cost_mods = total_mods_order * sel_mod["price_usd"]
cost_cards = n_cards * sel_card["price_usd"]
cost_psu = n_psu * sel_psu["price_usd"]
cost_hubs = n_hubs * HUB_PRICE_USD
total_usd = cost_mods + cost_cards + cost_psu + cost_hubs
total_rub_buy = total_usd * exchange_rate
total_rub_sell = area_m2 * price_per_m2

# ==========================================
# БЛОК 4: ОТЧЕТ
# ==========================================
st.markdown('<div class="section-header">📊 Финальный отчёт и Спецификация</div>', unsafe_allow_html=True)

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1: st.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mods_w} × {mods_h}</div></div>', unsafe_allow_html=True)
with col_m2: st.markdown(f'<div class="metric-card"><div class="metric-label">Рабочая мощн.</div><div class="metric-value">{avg_power_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m3: st.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${total_usd:,.0f}</div></div>', unsafe_allow_html=True)
with col_m4: st.markdown(f'<div class="metric-card" style="border-color:#4299e1;"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{total_rub_buy:,.0f}</div></div>', unsafe_allow_html=True)
with col_m5: st.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Продажа (₽)</div><div class="metric-value">{total_rub_sell:,.0f}</div></div>', unsafe_allow_html=True)

with st.expander("📦 Детализация комплектующих", expanded=True):
    c_list1, c_list2 = st.columns(2)
    with c_list1:
        st.write(f"**Модули:** {total_mods} + {res_mod} (ЗИП) = {total_mods_order} шт.")
        st.write(f"**Приемные карты:** {sel_card['name']} — {n_cards} шт.")
        if needs_hub: st.write(f"**Хабы HUB75E:** {n_hubs} шт.")
    with c_list2:
        st.write(f"**Блоки питания:** {sel_psu['name']} — {n_psu} шт.")
        st.write(f"**Процессор:** {processor} — 1 шт.")

with st.expander("🏗️ Конструктив и Сеть"):
    st.write(f"- **Магниты M6:** {total_mods * 4} шт.")
    st.write(f"- **Вертикальный профиль:** {mods_w + 1} шт. по {height_mm - 40} мм")
    st.write(f"- **Кабель ВВГ:** 3х{cable_sq} мм² (для 220В) или 5х{cable_sq} (для 380В)")
    st.write(f"- **Автомат защиты:** {breaker} А (тип C)")

# Figma Экспорт
st.markdown('<div class="section-header">🔗 Экспорт в Figma</div>', unsafe_allow_html=True)
figma_data = {
    "project": project_name, "dims": f"{width_mm}x{height_mm}", 
    "res": f"{int(width_mm/sel_mod['pitch'])}x{int(height_mm/sel_mod['pitch'])}",
    "buy_rub": round(total_rub_buy), "sell_rub": round(total_rub_sell)
}
st.code(json.dumps(figma_data, indent=2, ensure_ascii=False), language="json")

# Схема
st.subheader("📐 Схема сборки")
html_grid = f'<div style="display: grid; grid-template-columns: repeat({mods_w}, 1fr); gap: 2px; background-color: #2d3748; padding: 4px; width: 100%; max-width: 800px; border-radius: 4px; margin: 0 auto;">'
for _ in range(total_mods):
    html_grid += f'<div style="background-color: #48bb78; aspect-ratio: 2/1; border-radius: 2px;"></div>'
html_grid += "</div>"
st.components.v1.html(html_grid, height=int(800 * (mods_h/mods_w)) + 20)
