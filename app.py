import streamlit as st
import math, json, datetime, urllib.request
import xml.etree.ElementTree as ET

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Pro Calc | MediaLive", layout="wide", page_icon="🖥️")

# --- СОВРЕМЕННЫЙ CSS ДИЗАЙН ---
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

# --- ФУНКЦИЯ КУРСА ЦБ РФ ---
@st.cache_data(ttl=3600)
def get_cbr_usd_rate():
    try:
        url = "http://www.cbr.ru/scripts/XML_daily.asp"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            root = ET.fromstring(response.read())
        for valute in root.findall('Valute'):
            if valute.attrib.get('ID') == 'R01235':
                return round(float(valute.find('Value').text.replace(',', '.')) * 1.01, 2)
    except: pass
    return 100.0

# --- БАЗА КАРТ, БП И СИСТЕМ ---
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
    {"name": "Mean Well LRS-350-5", "price": 21.05},
    {"name": "A-200JQ-5 slim", "price": 13.57},
    {"name": "A-300FAR-4.5PH", "price": 27.31},
    {"name": "A-400JQ-4.5PH", "price": 17.69},
]

# !!! ВСТАВЬ СЮДА MODULES_DB ИЗ СЛЕДУЮЩЕГО СООБЩЕНИЯ !!!
MODULES_DB = [] 

# --- ЛОГИКА СОСТОЯНИЯ ---
if "w_in" not in st.session_state: st.session_state.w_in = 3840
if "h_in" not in st.session_state: st.session_state.h_in = 2240

def set_size(r): st.session_state.h_in = max(160, int(round((st.session_state.w_in / r) / 160)) * 160)

# --- ИНТЕРФЕЙС БОКОВОЙ ПАНЕЛИ ---
st.sidebar.header("💵 Финансы")
ex_rate = st.sidebar.number_input("Курс USD (ЦБ + 1%)", value=get_cbr_usd_rate())
price_per_m2 = st.sidebar.number_input("Цена продажи за м² (₽)", value=150000)

st.title("🖥️ LED MediaLive Pro Calculator")

# БЛОК 1: РАЗМЕРЫ
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
width_mm = c1.number_input("Ширина (мм)", min_value=320, step=320, key="w_in")
height_mm = c2.number_input("Высота (мм)", min_value=160, step=160, value=st.session_state.h_in)
st.session_state.h_in = height_mm

st.write("Быстрая подгонка:")
b1, b2, b3, b4 = st.columns(4)
if b1.button("16:9"): set_size(1.777); st.rerun()
if b2.button("4:3"): set_size(1.333); st.rerun()
if b3.button("21:9"): set_size(2.333); st.rerun()
if b4.button("1:1"): set_size(1.0); st.rerun()

# БЛОК 2: МОДУЛИ (ПОЯВЯТСЯ ПОСЛЕ ВСТАВКИ СПИСКА)
st.markdown('<div class="section-header">⚙️ 2. Матрица</div>', unsafe_allow_html=True)
if not MODULES_DB:
    st.error("Пожалуйста, вставь MODULES_DB во вторую часть кода!")
else:
    ce, ct = st.columns(2)
    env = ce.radio("Среда", ["Indoor", "Outdoor"], horizontal=True)
    techs = sorted(list(set(m["tech"] for m in MODULES_DB if m["env"] == env)))
    tech = ct.selectbox("Технология", techs)
    mods = [m for m in MODULES_DB if m["env"] == env and m["tech"] == tech]
    sel_mod = next(m for m in mods if m["name"] == st.selectbox("Модель модуля:", [x["name"] for x in mods]))

    # БЛОК 3: КОМПЛЕКТУЮЩИЕ
    st.markdown('<div class="section-header">🎛️ 3. Управление и Питание</div>', unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        cat = st.selectbox("Тип системы:", list(SYS_DB.keys()))
        sel_sys = next(s for s in SYS_DB[cat] if s["name"] == st.selectbox("Модель:", [x["name"] for x in SYS_DB[cat]]))
        power_phase = st.radio("Сеть", ["Одна фаза (220В)", "Три фазы (380В)"], horizontal=True)
    with cc2:
        sel_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == st.selectbox("Карта:", [x["name"] for x in RECEIVING_CARDS_DB], index=4))
        m_per_c = st.number_input("Мод/Карта:", value=12)
    with cc3:
        sel_psu = next(p for p in PSU_DB if p["name"] == st.selectbox("БП:", [x["name"] for x in PSU_DB]))
        m_per_p = st.number_input("Мод/БП:", value=8)

    # --- РАСЧЕТЫ ---
    mods_w, mods_h = width_mm // 320, height_mm // 160
    total_mods = mods_w * mods_h
    res_mod = math.ceil(total_mods * 0.05)
    n_cards = math.ceil(total_mods / m_per_c) + 1
    n_psu = math.ceil(total_mods / m_per_p) + 1
    n_hub = n_cards if sel_card["type"] == "A" else 0

    peak_kw = total_mods * sel_mod["max_power"] / 1000
    avg_kw = peak_kw * 0.35
    voltage = 220 if "Одна фаза" in power_phase else 380 * 1.732
    current = (peak_kw * 1200) / voltage
    sq = "1.5" if current < 15 else "2.5" if current < 21 else "4.0" if current < 27 else "6.0"

    # Деньги
    c_m = (total_mods + res_mod) * sel_mod["price_usd"]
    c_c = n_cards * sel_card["price_usd"]
    c_p = n_psu * sel_psu["price"]
    c_s = sel_sys["price"]
    c_h = n_hub * 4.10
    total_usd = c_m + c_c + c_p + c_s + c_h
    buy_rub = total_usd * ex_rate
    sell_rub = (width_mm * height_mm / 1_000_000) * price_per_m2

    # --- ФИНАЛЬНЫЙ ОТЧЕТ ---
    st.markdown('<div class="section-header">📊 Финальный отчёт</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.markdown(f'<div class="metric-card"><div class="metric-label">Сетка</div><div class="metric-value">{mods_w}x{mods_h}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-label">Раб. Мощность</div><div class="metric-value">{avg_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-label">Закупка ($)</div><div class="metric-value">${total_usd:,.0f}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label">Закупка (₽)</div><div class="metric-value">{buy_rub:,.0f}</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-card"><div class="metric-label">Продажа (₽)</div><div class="metric-value">{sell_rub:,.0f}</div></div>', unsafe_allow_html=True)

    with st.expander("📦 Спецификация и Инженерия", expanded=True):
        st.write(f"- **Модули:** {total_mods}+{res_mod} шт | **БП:** {n_psu} шт | **Карты:** {n_cards} шт")
        if n_hub: st.write(f"- **Хабы HUB75E:** {n_hub} шт.")
        st.write(f"- **Магниты:** {total_mods*4} шт | **Верт. профиль:** {mods_w+1} шт")
        st.write(f"- **Электрика:** Кабель 3х{sq} мм² | Ток: {current:.1f} А")

    st.subheader("📐 Схема сборки")
    grid = f'<div style="display: grid; grid-template-columns: repeat({mods_w}, 1fr); gap: 2px; background:#2d3748; padding:4px; max-width:800px; margin:auto;">'
    for _ in range(total_mods): grid += '<div style="background:#48bb78; aspect-ratio:2/1;"></div>'
    st.components.v1.html(grid + "</div>", height=int(800*(mods_h/mods_w))+40)
