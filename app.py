import streamlit as st
import math, json, datetime, urllib.request
import xml.etree.ElementTree as ET

# --- ЭТАЛОННЫЕ БАЗЫ ДАННЫХ (ОПРЕДЕЛЕНЫ ПЕРВЫМИ) ---
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
RECEIVING_CARDS_DB = [
    {"name": "MRV 208", "price_usd": 13.29, "type": "M"}, {"name": "MRV 412", "price_usd": 15.40, "type": "M"},
    {"name": "MRV 416", "price_usd": 16.09, "type": "M"}, {"name": "MRV 532", "price_usd": 21.00, "type": "M"},
    {"name": "A5s Plus", "price_usd": 17.02, "type": "A"}, {"name": "A7s Plus", "price_usd": 19.12, "type": "A"},
    {"name": "A8s", "price_usd": 33.89, "type": "A"}, {"name": "A10s Plus", "price_usd": 44.57, "type": "A"}
]
HUBS_DB = [{"name": "HUB 75Е-AXS", "price_usd": 14.86}, {"name": "HUB 320-AXS", "price_usd": 14.86}]
PSU_DB = [
    {"name": "LRS-200-5", "price": 15.58}, {"name": "A-200JQ slim", "price": 13.57},
    {"name": "A-300FAR", "price": 27.31}, {"name": "A-400JQ slim", "price": 17.69}
]
PROCESSORS = ["VX400", "VX600 Pro", "VX1000 Pro", "VX16S", "VC4", "VC10", "TB30", "TB60"]

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Pro Calc | MediaLive", layout="wide")

# --- СТИЛИ ---
st.markdown("""<style>
    .reportview-container { background: #0e1117; }
    .metric-card { background: linear-gradient(135deg, #1e2530 0%, #151a22 100%); border-radius:10px; padding:20px; text-align:center; border:1px solid #2d3748; margin-bottom:20px; }
    .metric-value { font-size:24px; font-weight:bold; color:#63b3ed; }
    .metric-label { font-size:13px; color:#a0aec0; text-transform:uppercase; }
    .section-header { color:#e2e8f0; font-size:1.25rem; font-weight:600; margin-top:1.5rem; border-bottom:1px solid #2d3748; padding-bottom:5px; }
</style>""", unsafe_allow_html=True)

# --- КУРС ЦБ ---
@st.cache_data(ttl=3600)
def get_rate():
    try:
        with urllib.request.urlopen("http://www.cbr.ru/scripts/XML_daily.asp", timeout=5) as r:
            root = ET.fromstring(r.read())
        for v in root.findall('Valute'):
            if v.attrib.get('ID') == 'R01235': return round(float(v.find('Value').text.replace(',', '.')) * 1.01, 2)
    except: pass
    return 105.0

# --- СОСТОЯНИЕ ---
if "w_in" not in st.session_state: st.session_state.w_in = 3840
if "h_in" not in st.session_state: st.session_state.h_in = 2240

def set_size(r): st.session_state.h_in = max(160, int(round((st.session_state.w_in / r) / 160)) * 160)

# --- ИНТЕРФЕЙС ---
st.sidebar.header("💵 Финансы")
rate = st.sidebar.number_input("Курс USD (ЦБ+1%)", value=get_rate())
p_m2 = st.sidebar.number_input("Цена продажи/м² (₽)", value=150000)

st.title("🖥️ MediaLive LED Calculator")

st.markdown('<div class="section-header">📏 1. Геометрия</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
w_mm = c1.number_input("Ширина (мм)", step=320, key="w_in")
h_mm = c2.number_input("Высота (мм)", step=160, value=st.session_state.h_in)
st.session_state.h_in = h_mm
st.write("Подгонка:")
b1, b2, b3, b4 = st.columns(4)
if b1.button("16:9"): set_size(1.777); st.rerun()
if b2.button("4:3"): set_size(1.333); st.rerun()
if b3.button("21:9"): set_size(2.333); st.rerun()
if b4.button("1:1"): set_size(1.0); st.rerun()

st.markdown('<div class="section-header">⚙️ 2. Матрица</div>', unsafe_allow_html=True)
ce, ct = st.columns(2)
env = ce.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
techs = sorted(list(set(m["tech"] for m in MODULES_DB if m["env"] == env)))
tech = ct.selectbox("Технология", techs)
mods = [m for m in MODULES_DB if m["env"] == env and m["tech"] == tech]
sel_mod = next(m for m in mods if m["name"] == st.selectbox("Модель модуля:", [x["name"] for x in mods]))

st.markdown('<div class="section-header">🎛️ 3. Электроника</div>', unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns(3)
with cc1:
    proc = st.selectbox("Процессор:", PROCESSORS, index=2)
    m_p_c = st.number_input("Мод/Карту:", value=12)
with cc2:
    sel_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == st.selectbox("Карта:", [x["name"] for x in RECEIVING_CARDS_DB], index=4))
    hub_name, hub_p = "Нет", 0.0
    if sel_card["type"] == "A":
        hub_name = st.selectbox("HUB для серии A:", [h["name"] for h in HUBS_DB])
        hub_p = next(h["price_usd"] for h in HUBS_DB if h["name"] == hub_name)
with cc3:
    sel_psu = next(p for p in PSU_DB if p["name"] == st.selectbox("БП:", [x["name"] for x in PSU_DB], index=1))
    m_p_p = st.number_input("Мод/БП:", value=8)

# --- РАСЧЕТЫ ---
mw, mh = w_mm // 320, h_mm // 160
total_m = mw * mh
res_m = math.ceil(total_m * 0.05)
n_c = math.ceil(total_m / m_p_c) + 1
n_p = math.ceil(total_m / m_p_p) + 1
n_h = n_c if sel_card["type"] == "A" else 0

peak_kw = (total_m * sel_mod["max_power"]) / 1000
area = (w_mm * h_mm) / 1000000
buy_u = ((total_m + res_m) * sel_mod["price_usd"]) + (n_c * sel_card["price_usd"]) + (n_p * sel_psu["price"]) + (n_h * hub_p)
buy_r = buy_u * rate
sell_r = area * p_m2

# --- ОТЧЕТ ---
st.markdown('<div class="section-header">📊 Отчёт</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mw}x{mh}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Мощность(Раб)</div><div class="metric-value">{peak_kw*0.35:.1f}кВт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Закуп $</div><div class="metric-value">${buy_u:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Закуп ₽</div><div class="metric-value">{buy_r:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="metric-card"><div class="metric-label">Продажа ₽</div><div class="metric-value">{sell_r:,.0f}</div></div>', unsafe_allow_html=True)

with st.expander("📝 Спецификация и Инженерия", expanded=True):
    st.write(f"- **Комплекты:** Модули: {total_m}+{res_m} шт | Карты: {n_c} шт | БП: {n_p} шт | HUB: {n_h if n_h>0 else 'встр.'}")
    st.write(f"- **Конструктив:** Магниты: {total_m*4} шт | Верт. профиль: {mw+1} шт по {h_mm-40} мм")
    st.write(f"- **Электрика:** Ток пиковый: {(peak_kw*1000)/220:.1f} А | Кабель: 3х{'2.5' if peak_kw<4 else '4.0' if peak_kw<6 else '6.0'} мм²")

st.markdown('<div class="section-header">📐 Визуализация</div>', unsafe_allow_html=True)
grid = f'<div style="display:grid; grid-template-columns:repeat({mw}, 1fr); gap:2px; background:#2d3748; padding:4px; max-width:800px; margin:auto;">'
for _ in range(total_m): grid += '<div style="background:#48bb78; aspect-ratio:2/1;"></div>'
st.components.v1.html(grid + "</div>", height=int(800*(mh/mw))+40)
