import streamlit as st
import math, json, datetime, urllib.request
import xml.etree.ElementTree as ET

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Pro Calc | MediaLive", layout="wide", page_icon="🖥️")

# --- СТИЛИ ---
st.markdown("""
<style>
    .metric-card { background: linear-gradient(135deg, #1e2530 0%, #151a22 100%); border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #2d3748; margin-bottom: 20px; }
    .metric-value { font-size: 22px; font-weight: bold; color: #63b3ed; }
    .metric-label { font-size: 11px; color: #a0aec0; text-transform: uppercase; }
    .section-header { color: #e2e8f0; font-size: 1.2rem; font-weight: 600; margin-top: 1.5rem; border-bottom: 1px solid #2d3748; padding-bottom: 5px; margin-bottom: 15px; }
    .stButton>button { background: linear-gradient(90deg, #3182ce, #2b6cb0); color: white; border-radius: 8px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- КУРС ЦБ + 1% ---
@st.cache_data(ttl=3600)
def get_rate():
    try:
        with urllib.request.urlopen("http://www.cbr.ru/scripts/XML_daily.asp", timeout=5) as r:
            root = ET.fromstring(r.read())
        for v in root.findall('Valute'):
            if v.attrib.get('ID') == 'R01235':
                return round(float(v.find('Value').text.replace(',', '.')) * 1.01, 2)
    except: pass
    return 100.0

# --- БАЗЫ ДАННЫХ (СЖАТЫЕ) ---
MODULES = [
    {'n': 'Qiangli Q1.25 Indoor 3840Hz', 'e': 'Indoor', 'p': 1.25, 't': 'SMD', 'w': 30, 'usd': 45.01},
    {'n': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'e': 'Indoor', 'p': 1.25, 't': 'GOB', 'w': 30, 'usd': 51.13},
    {'n': 'Qiangli R1.5 Indoor 6000Hz (Гибкий)', 'e': 'Indoor', 'p': 1.5, 't': 'Гибкий', 'w': 23, 'usd': 33.45},
    {'n': 'Qiangli Q1.53 Indoor 3840Hz', 'e': 'Indoor', 'p': 1.53, 't': 'SMD', 'w': 30, 'usd': 29.43},
    {'n': 'VISTECH P1.53 COB Indoor 3840Hz', 'e': 'Indoor', 'p': 1.53, 't': 'COB', 'w': 30, 'usd': 42.4},
    {'n': 'Qiangli Q1.86 Indoor 3840Hz', 'e': 'Indoor', 'p': 1.86, 't': 'SMD', 'w': 23, 'usd': 18.64},
    {'n': 'Qiangli Q2 Indoor 3840Hz', 'e': 'Indoor', 'p': 2.0, 't': 'SMD', 'w': 23, 'usd': 16.63},
    {'n': 'Qiangli Q2.5 Indoor 3840Hz', 'e': 'Indoor', 'p': 2.5, 't': 'SMD', 'w': 24, 'usd': 12.55},
    {'n': 'Qiangli Q3.07 Indoor 1920Hz', 'e': 'Indoor', 'p': 3.07, 't': 'SMD', 'w': 22, 'usd': 8.98},
    {'n': 'Qiangli Q4 Indoor 1920Hz', 'e': 'Indoor', 'p': 4.0, 't': 'SMD', 'w': 24, 'usd': 7.56},
    {'n': 'Qiangli Q2.5 Outdoor 3840Hz', 'e': 'Outdoor', 'p': 2.5, 't': 'SMD', 'w': 33, 'usd': 24.39},
    {'n': 'Qiangli Q3.07 Outdoor 2880Hz', 'e': 'Outdoor', 'p': 3.07, 't': 'SMD', 'w': 40, 'usd': 15.28},
    {'n': 'Qiangli Q4 Outdoor 2880Hz', 'e': 'Outdoor', 'p': 4.0, 't': 'SMD', 'w': 47, 'usd': 11.02},
    {'n': 'Qiangli Q5 Outdoor 2880Hz', 'e': 'Outdoor', 'p': 5.0, 't': 'SMD', 'w': 43, 'usd': 9.09},
    {'n': 'Qiangli Q8 Outdoor 2880Hz', 'e': 'Outdoor', 'p': 8.0, 't': 'SMD', 'w': 44, 'usd': 7.62},
]

CARDS = [
    {"n": "MRV 208-1 / MRV 208-N", "u": 10.66, "t": "M"},
    {"n": "MRV 412", "u": 15.17, "t": "M"},
    {"n": "MRV 416", "u": 15.57, "t": "M"},
    {"n": "A5s Plus", "u": 19.68, "t": "A"},
    {"n": "A8s / A8s-N", "u": 51.25, "t": "A"},
    {"n": "A10s Plus-N", "u": 72.56, "t": "A"},
]

SYS_DB = {
    "Видеопроцессор": [{"n": "VX400", "u": 889.92}, {"n": "VX600", "u": 987.77}, {"n": "VX1000", "u": 1357.54}, {"n": "VC4", "u": 179.22}, {"n": "VC10", "u": 889.92}],
    "Синхронный": [{"n": "MSD 300", "u": 100.63}, {"n": "MCTRL 300", "u": 155.53}, {"n": "MCTRL 600", "u": 278.31}, {"n": "MX30", "u": 2228.28}],
    "Асинхронный": [{"n": "TB10 Plus", "u": 58.61}, {"n": "TB30", "u": 236.39}, {"n": "TB40", "u": 181.28}, {"n": "TB60", "u": 404.58}]
}

PSU = [{"n": "Mean Well LRS-200-5", "u": 15.58}, {"n": "A-200JQ-5 slim", "u": 13.57}, {"n": "A-400JQ-4.5PH", "u": 17.69}]

# --- СОСТОЯНИЕ ---
if "w" not in st.session_state: st.session_state.w = 3840
if "h" not in st.session_state: st.session_state.h = 2240

# --- ИНТЕРФЕЙС ---
st.sidebar.header("💵 Финансы")
rate = st.sidebar.number_input("Курс USD (ЦБ+1%)", value=get_rate())
p_m2 = st.sidebar.number_input("Цена продажи/м² (₽)", value=150000)

st.title("🖥️ LED Pro Calculator | MediaLive")

st.markdown('<div class="section-header">📏 1. Геометрия</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
w_mm = c1.number_input("Ширина (мм)", step=320, key="w")
h_mm = c2.number_input("Высота (мм)", step=160, key="h")

st.markdown('<div class="section-header">⚙️ 2. Модули</div>', unsafe_allow_html=True)
ce, ct = st.columns(2)
env = ce.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
techs = sorted(list(set(m['t'] for m in MODULES if m['e'] == env)))
tech = ct.selectbox("Технология", techs)
mods = [m for m in MODULES if m['e'] == env and m['t'] == tech]
sel_mod = next(m for m in mods if m['n'] == st.selectbox("Модель модуля Qiangli:", [x['n'] for x in mods]))

st.markdown('<div class="section-header">🎛️ 3. Электроника</div>', unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns(3)
with cc1:
    cat = st.selectbox("Управление:", list(SYS_DB.keys()))
    sel_sys = next(s for s in SYS_DB[cat] if s['n'] == st.selectbox("Модель:", [x['n'] for x in SYS_DB[cat]]))
with cc2:
    sel_card = next(c for c in CARDS if c['n'] == st.selectbox("Карта:", [x['n'] for x in CARDS], index=3))
    m_per_c = st.number_input("Мод/Карта:", value=12)
with cc3:
    sel_psu = next(p for p in PSU if p['n'] == st.selectbox("БП:", [x['n'] for x in PSU]))
    m_per_p = st.number_input("Мод/БП:", value=8)

# --- РАСЧЕТЫ ---
mw, mh = w_mm // 320, h_mm // 160
total_m = mw * mh
res_m = math.ceil(total_m * 0.05)
n_card = math.ceil(total_m / m_per_c) + 1
n_psu = math.ceil(total_m / m_per_p) + 1
n_hub = n_card if sel_card['t'] == "A" else 0

peak_kw = (total_m * sel_mod['w']) / 1000
current = (peak_kw * 1000) / 220
sq = "1.5" if current < 15 else "2.5" if current < 21 else "4.0" if current < 27 else "6.0"

# Деньги
buy_usd = ((total_m + res_m) * sel_mod['usd']) + (n_card * sel_card['u']) + (n_psu * sel_psu['u']) + sel_sys['u'] + (n_hub * 4.10)
buy_rub = buy_usd * rate
sell_rub = (w_mm * h_mm / 1000000) * p_m2

# --- ОТЧЕТ ---
st.markdown('<div class="section-header">📊 Результаты</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mw}x{mh}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-label">Мощность(Раб)</div><div class="metric-value">{peak_kw*0.35:.1f} кВт</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${buy_usd:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{buy_rub:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="metric-card"><div class="metric-label">Продажа (₽)</div><div class="metric-value">{sell_rub:,.0f}</div></div>', unsafe_allow_html=True)

with st.expander("📝 Спецификация", expanded=True):
    col_a, col_b = st.columns(2)
    col_a.write(f"**Комплектующие:**\n- Модули: {total_m} + {res_m} ЗИП\n- Карты: {n_card} шт\n- БП: {n_psu} шт\n- Хабы HUB75: {n_hub} шт")
    col_b.write(f"**Конструктив:**\n- Магниты: {total_m*4} шт\n- Профиль верт.: {mw+1} шт\n- Кабель: ВВГ 3х{sq}\n- Ток: {current:.1f}А")

st.markdown('<div class="section-header">🔗 Экспорт в Figma</div>', unsafe_allow_html=True)
st.code(json.dumps({"project": "MediaLive", "dims": f"{w_mm}x{h_mm}", "res": f"{int(w_mm/sel_mod['p'])}x{int(h_mm/sel_mod['p'])}", "buy": round(buy_rub), "sell": round(sell_rub)}, indent=2), language="json")

st.subheader("📐 Схема модулей")
grid = f'<div style="display: grid; grid-template-columns: repeat({mw}, 1fr); gap: 2px; background:#2d3748; padding:4px; max-width:800px; margin:auto;">'
for _ in range(total_m): grid += '<div style="background:#48bb78; aspect-ratio:2/1;"></div>'
st.components.v1.html(grid + "</div>", height=int(800*(mh/mw))+40)
