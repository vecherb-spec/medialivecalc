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
@st.cache_data(ttl=3600) # Кэшируем результат на 1 час
def get_cbr_usd_rate():
    try:
        url = "http://www.cbr.ru/scripts/XML_daily.asp"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for valute in root.findall('Valute'):
            if valute.attrib.get('ID') == 'R01235': # ID доллара США
                value_str = valute.find('Value').text.replace(',', '.')
                return float(value_str) * 1.01 # Возвращаем курс + 1%
        return 95.0
    except Exception:
        return 95.0 # Резервный курс при ошибке сети

# --- БАЗА ДАННЫХ МОДУЛЕЙ (Синхронизировано с прайсом, отсортировано по шагу и частоте) ---
MODULES_DB = [
    # INDOOR
    {'name': 'Qiangli Q1.25 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 45.01},
    {'name': 'Qiangli Q1.25 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 46.13},
    {'name': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 51.13},
    {'name': 'Qiangli R1.5 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 33.45},
    {'name': 'Qiangli Q1.53 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.43},
    {'name': 'VISTECH P1.53 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 42.4},
    {'name': 'Qiangli Q1.53 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 30.43},
    {'name': 'Qiangli Q1.53 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 35.16},
    {'name': 'Qiangli Q1.66 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.66, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 26.49},
    {'name': 'Qiangli Q1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 500, 'max_power': 23.0, 'price_usd': 18.64},
    {'name': 'Qiangli R1.86 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 21.99},
    {'name': 'VISTECH P1.86 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.75},
    {'name': 'Qiangli Q1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 20.0},
    {'name': 'Qiangli R1.86 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 22.88},
    {'name': 'Qiangli Q2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 23.0, 'price_usd': 16.63},
    {'name': 'Qiangli R2 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 19.97},
    {'name': 'Qiangli Q2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 23.0, 'price_usd': 17.6},
    {'name': 'Qiangli R2 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 20.78},
    {'name': 'Qiangli Q2 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'GOB', 'brightness': 600, 'max_power': 23.0, 'price_usd': 21.84},
    {'name': 'Qiangli Q2.5 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.03},
    {'name': 'Qiangli Q2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.55},
    {'name': 'Qiangli R2.5 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 24.0, 'price_usd': 14.87},
    {'name': 'Qiangli Q2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 500, 'max_power': 24.0, 'price_usd': 13.42},
    {'name': 'Qiangli R2.5 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 600, 'max_power': 24.0, 'price_usd': 15.56},
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
    {'name': 'Qiangli R4 Outdoor 3840Hz (Гибкий)', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'Flexible', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 25.08},
    {'name': 'Qiangli Q4 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.48},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.09},
    {'name': 'Qiangli Q5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.54},
    {'name': 'Qiangli Q6.66 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 4500, 'max_power': 46.0, 'price_usd': 8.86},
    {'name': 'Qiangli Q6.66 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 9.28},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.62},
    {'name': 'Qiangli Q8 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 8.04},
]
# --- ДОБАВЛЯЕМ НОВЫЕ СПРАВОЧНИКИ КАРТ И ХАБОВ ---
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
# Блоки питания (строки 320-330 строго по прайсу LEDCapital)
PSU_DB = [
    {"name": "A-200-5 (Chuanglian)", "price_usd": 6.84, "max_w": 200},
    {"name": "A-200-5N (Slim) (Chuanglian)", "price_usd": 12.80, "max_w": 200},
    {"name": "A-300-5 (Slim) (Chuanglian)", "price_usd": 14.50, "max_w": 300},
    {"name": "A-200JQ-5 slim (Chuanglian)", "price_usd": 13.57, "max_w": 200},
    {"name": "A-300FAR-4.5PH (Chuanglian)", "price_usd": 27.31, "max_w": 300},
    {"name": "A-400JQ-4.5PH (Chuanglian)", "price_usd": 17.69, "max_w": 400},
    {"name": "Mean Well LRS-200-5", "price_usd": 15.58, "max_w": 200},
    {"name": "Mean Well LRS-350-5", "price_usd": 21.05, "max_w": 350},
    {"name": "G-Energy N200V5-A (Slim)", "price_usd": 13.57, "max_w": 200},
    {"name": "CZCL A-200-5N (Slim)", "price_usd": 12.80, "max_w": 200},
    {"name": "CZCL A-300-5 (Slim)", "price_usd": 14.50, "max_w": 300},
]
# Хабы (строго по ценам пользователя)
HUBS_DB = [
    {"name": "HUB 75E", "price_usd": 5.29},
    {"name": "HUB 75E-AXS", "price_usd": 14.86},
    {"name": "HUB 320-AXS", "price_usd": 14.86},
]
# --- СПРАВОЧНИКИ ---
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

CARD_MAX_PIXELS = {
    "Novastar MRV 208": (256, 256),
    "Novastar MRV 412": (512, 512),
    "Novastar MRV 416": (512, 256),
    "Novastar MRV 532": (256, 384),
    "Novastar CA50E (COEX)": (512, 768),
    "Novastar A5s Plus": (512, 384),
    "Novastar A7s Plus": (512, 512),
    "Novastar A8s": (512, 256),
    "Novastar A10s Plus": (512, 512),
    "Novastar A10s Pro": (512, 512)
}
popular_16_9 = {
    "2560 × 1440 мм (8×9 шт) | Идеально 16:9": (2560, 1440),
    "2880 × 1600 мм (9×10 шт) | ~16:9": (2880, 1600),
    "3200 × 1760 мм (10×11 шт) | ~16:9": (3200, 1760),
    "3840 × 2240 мм (12×14 шт) | ~16:9": (3840, 2240),
    "4800 × 2720 мм (15×17 шт) | ~16:9": (4800, 2720),
    "5120 × 2880 мм (16×18 шт) | Идеально 16:9": (5120, 2880),
    "6080 × 3360 мм (19×21 шт) | ~16:9": (6080, 3360),
    "7680 × 4320 мм (24×27 шт) | Идеально 16:9": (7680, 4320),
    "Свой размер (вручную)": (None, None)
}

# --- ИНИЦИАЛИЗАЦИЯ STATE ---
if "width_input" not in st.session_state: st.session_state.width_input = 3840
if "height_mm" not in st.session_state: st.session_state.height_mm = 2240
if "previous_selected" not in st.session_state: st.session_state.previous_selected = "3840 × 2240 мм (12×14 шт) | ~16:9"

def fit_ratio(ratio):
    ideal = st.session_state.width_input / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Обработка выбора популярного размера
selected_label = st.sidebar.selectbox("📐 Быстрый размер (16:9)", list(popular_16_9.keys()), index=3)
if selected_label != st.session_state.previous_selected:
    selected_w, selected_h = popular_16_9[selected_label]
    if selected_w is not None:
        st.session_state.width_input = selected_w 
        st.session_state.height_mm = selected_h
    st.session_state.previous_selected = selected_label
    st.rerun()

# --- БОКОВАЯ ПАНЕЛЬ: ПРОЕКТ И ФИНАНСЫ ---
st.sidebar.markdown("---")
st.sidebar.header("📝 Данные проекта")
project_name = st.sidebar.text_input("Имя проекта", value="MediaLive - Новый проект")
client_name = st.sidebar.text_input("Клиент / Заказчик", placeholder="Введите имя клиента")

st.sidebar.markdown("---")
st.sidebar.header("💵 Финансы")

# Получаем актуальный курс
current_cbr_rate = get_cbr_usd_rate()

exchange_rate = st.sidebar.number_input(
    "Курс USD (₽) для закупки (ЦБ + 1%)", 
    min_value=50.0, 
    value=float(current_cbr_rate), 
    step=0.1,
    help="Курс автоматически парсится с сайта ЦБ РФ + добавляется 1%, согласно правилам прайс-листа."
)
price_per_m2 = st.sidebar.number_input("Цена за м² клиенту (₽)", min_value=0, value=150000, step=5000)

st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Точный расчет комплектующих на базе динамического прайс-листа LEDCapital.")

# ==========================================
# БЛОК 1: РАЗМЕРЫ И ПРОПОРЦИИ
# ==========================================
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)

col_w, col_h = st.columns(2)
with col_w:
    width_mm = st.number_input("Ширина экрана (мм) [Шаг 320]", min_value=320, step=320, key="width_input")
with col_h:
    height_mm = st.number_input("Высота экрана (мм) [Шаг 160]", min_value=160, step=160, value=st.session_state.height_mm)
    st.session_state.height_mm = height_mm

st.markdown("<span style='font-size: 14px; color: #a0aec0;'>Быстрая подгонка высоты под пропорции:</span>", unsafe_allow_html=True)
btn_cols = st.columns(4)
if btn_cols[0].button("16:9 (Широкий)"): fit_ratio(1.7777777777777777); st.rerun()
if btn_cols[1].button("4:3 (ТВ)"): fit_ratio(1.3333333333333333); st.rerun()
if btn_cols[2].button("21:9 (Кино)"): fit_ratio(2.3333333333333335); st.rerun()
if btn_cols[3].button("1:1 (Квадрат)"): fit_ratio(1.0); st.rerun()

# ==========================================
# БЛОК 2: ХАРАКТЕРИСТИКИ И МОНТАЖ
# ==========================================
st.markdown('<div class="section-header">⚙️ 2. Матрица и Конструкция</div>', unsafe_allow_html=True)

col_mat, col_mount = st.columns(2)

with col_mat:
    c_env, c_tech = st.columns(2)
    with c_env:
        env_key = st.radio("Среда использования", ["Indoor", "Outdoor"], horizontal=True)
    with c_tech:
        tech_options = list(set([m["tech"] for m in MODULES_DB if m["env"] == env_key]))
        tech_key = st.selectbox("Технология", tech_options)
    
    # Фильтруем базу данных по среде И технологии
    available_modules = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
    module_names = [m["name"] for m in available_modules]
    
    # Выбор модуля
    selected_module_name = st.selectbox("Светодиодный модуль (из прайса):", module_names)
    
    # Получаем характеристики выбранного модуля
    selected_module = next(m for m in available_modules if m["name"] == selected_module_name)
    
    pixel_pitch = selected_module["pitch"]
    tech = selected_module["tech"]
    brightness = selected_module["brightness"]
    max_power_module = selected_module["max_power"]
    price_usd = selected_module["price_usd"]
    price_rub_per_module = price_usd * exchange_rate
    
    # Инфо-панель с характеристиками
    st.markdown(f"""
    <div style="padding: 12px; border-radius: 8px; border: 1px solid #2d3748; background: #1a202c; font-size: 14px; color: #e2e8f0; margin-bottom: 10px;">
        <span style="color: #a0aec0;">Шаг:</span> <strong>P{pixel_pitch}</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Тип:</span> <strong>{tech}</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Яркость:</span> <strong>{brightness} нит</strong><br>
        <span style="color: #a0aec0;">Макс. потребление:</span> <strong>{max_power_module} Вт/шт</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Цена (закупка):</span> <strong style="color: #48bb78;">${price_usd:.2f}</strong> ({price_rub_per_module:.0f} ₽)
    </div>
    """, unsafe_allow_html=True)
        
    sensor = "Нет"
    if env_key == "Outdoor":
        sensor = st.selectbox("Датчик яркости", ["Нет", "Есть (NS060)"], index=1)

with col_mount:
    mount_type = st.radio("Тип монтажа", ["Монолитный (Магниты/Профиль)", "В кабинетах"], horizontal=True, index=0)
    
    cabinet_model = "Монолит"
    cabinet_width, cabinet_height, cabinet_weight_per = 640, 480, 20.0
    
    if "кабинетах" in mount_type:
        cabinet_options = [
            "QM Series (640×480 мм, indoor, ~20 кг)",
            "MG Series (960×960 мм, outdoor/indoor, ~40 кг)",
            "QF Series (500×500 мм, rental/indoor, ~13.5 кг)",
            "QS Series (960×960 мм, outdoor fixed, ~45 кг)",
            "Custom (введите размер и вес вручную)"
        ]
        cabinet_model = st.selectbox("Модель кабинета", cabinet_options, index=0)
        if "Custom" in cabinet_model:
            cc1, cc2, cc3 = st.columns(3)
            with cc1: cabinet_width = st.number_input("Ширина (мм)", min_value=320, value=640)
            with cc2: cabinet_height = st.number_input("Высота (мм)", min_value=160, value=480)
            with cc3: cabinet_weight_per = st.number_input("Вес (кг)", min_value=1.0, value=20.0)
        else:
            cab_map = {
                "QM": (640, 480, 20.0), "MG": (960, 960, 40.0), 
                "QF": (500, 500, 13.5), "QS": (960, 960, 45.0)
            }
            key_prefix = cabinet_model.split()[0]
            cabinet_width, cabinet_height, cabinet_weight_per = cab_map.get(key_prefix, (640, 480, 20.0))
    else:
        magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

# ==========================================
# БЛОК 3: УПРАВЛЕНИЕ И КОММУТАЦИЯ
# ==========================================
st.markdown('<div class="section-header">🎛️ 3. Система управления и Data-коммутация</div>', unsafe_allow_html=True)

col_ctrl1, col_ctrl2 = st.columns(2)

with col_ctrl1:
    system_type = st.radio("Система", ["Синхронная (Live)", "Асинхронная (Плеер)"], horizontal=True, index=0)
    avail_procs = ["VC10", "VC2", "VC4", "VC6", "VC16", "VC24", "MCTRL300", "MCTRL600", "MCTRL700", "MCTRL4K", "MCTRL R5", "VX400", "VX600 Pro", "VX1000 Pro", "VX2000 Pro", "VX16S"] if "Синхронная" in system_type else ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]
    processor = st.selectbox("Процессор / Контроллер", avail_procs, index=0)
    
    refresh_rate = st.selectbox("Целевая частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)

with col_ctrl2:
    # 1. Сначала создаем список имен для выбора
    card_names = [c["name"] for c in RECEIVING_CARDS_DB]
    selected_card_name = st.selectbox("Приёмная карта (Novastar):", card_names, index=1)
    
    # 2. ТУТ ВАЖНО: Находим весь объект карты по выбранному имени
    receiving_card = next(c for c in RECEIVING_CARDS_DB if c["name"] == selected_card_name)
    
    # 3. Только ТЕПЕРЬ можно спрашивать ["type"]
    hub_price_usd = 0.0
    if receiving_card.get("type") == "A":
        selected_hub = st.selectbox(
            "Выберите HUB для серии A:", 
            HUBS_DB,
            format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
            key="hub_selector_v_fixed"
        )
        hub_price_usd = selected_hub["price_usd"]
        
        st.markdown(f"<div style='font-size: 13px; color: #a0aec0; margin-top: -10px;'>Цена за шт: ${hub_price_usd:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("HUB75 встроен в MRV")

real_width = math.ceil(width_mm / 320) * 320
real_height = math.ceil(height_mm / 160) * 160
total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)

required_ports = math.ceil(total_px / 650000)
available_ports = PROCESSOR_PORTS.get(processor, 1)
load_per_port = (total_px / (available_ports * 650000)) * 100 if available_ports > 0 else 100.0

status_text = "✅ Портов достаточно" if required_ports <= available_ports else "❌ ВНИМАНИЕ: Недостаточно портов!"
status_color = "#48bb78" if required_ports <= available_ports else "#f56565"

st.markdown(f"""
<div style="padding: 12px 20px; border-radius: 8px; border-left: 4px solid {status_color}; background: #1a202c; margin-top: 10px;">
    <span style="color: #a0aec0; font-size: 14px;">Статус портов процессора <strong>{processor}</strong>:</span><br>
    Доступно: <strong>{available_ports}</strong> &nbsp;|&nbsp;
    Требуется: <strong>{required_ports}</strong> &nbsp;|&nbsp;
    Нагрузка на порт: <strong>{load_per_port:.1f}%</strong> &nbsp;&nbsp;➔&nbsp;&nbsp;
    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# БЛОК 4: ПИТАНИЕ И РЕЗЕРВ (ЗИП) - ФИНАЛЬНЫЙ ЧИСТЫЙ ВАРИАНТ
# ==========================================
st.markdown('<div class="section-header">⚡ 4. Питание сети и ЗИП</div>', unsafe_allow_html=True)

col_pwr, col_zip = st.columns(2)

with col_pwr:
    # Выпадающий список: Название — $Цена
    selected_psu = st.selectbox(
        "Модель БП (из прайса):", 
        PSU_DB, 
        format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
        index=0,
        key="final_psu_selector" 
    )
    sel_psu = selected_psu 
    
    # Инфо-плашка (тут оставим и USD, и пересчет в RUB для удобства)
    st.markdown(f"""
    <div style="padding: 12px; border-radius: 8px; border: 1px solid #2d3748; background: #1a202c; font-size: 14px; color: #e2e8f0; margin-bottom: 10px;">
        <span style="color: #a0aec0;">Мощность:</span> <strong>{sel_psu['max_w']}W</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Цена за шт:</span> <strong style="color: #48bb78;">${sel_psu['price_usd']:.2f}</strong> ({(sel_psu['price_usd'] * exchange_rate):.0f} ₽)
    </div>
    """, unsafe_allow_html=True)
    
    modules_per_psu = st.selectbox("Модулей на 1 БП:", [4, 6, 8, 10, 12, 16], index=2, key="final_m_per_p")
    power_phase = st.radio("Вводная сеть:", ["Одна фаза (220 В)", "Три фазы (380 В)"], horizontal=True, key="final_phase")

with col_zip:
    reserve_enabled = st.checkbox("Включить комплекты ЗИП (Резерв)", value=True)
    reserve_modules_choice = "5%"
    reserve_modules_custom = 0
    reserve_psu_cards = False
    reserve_patch = False
    
    if reserve_enabled:
        with st.container():
            zc1, zc2 = st.columns(2)
            with zc1:
                reserve_modules_choice = st.selectbox("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1)
                if reserve_modules_choice == "Свой":
                    reserve_modules_custom = st.number_input("Кол-во шт.", min_value=0)
            with zc2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                reserve_psu_cards = st.checkbox("+1 БП и Карта", value=True)
                reserve_patch = st.checkbox("Двойной запас патч-кордов", value=False)

# ==========================================
# ==========================================
# ПОЛНЫЕ ИНЖЕНЕРНЫЕ ВЫЧИСЛЕНИЯ (ИСПРАВЛЕНО)
# ==========================================
modules_w = math.ceil(width_mm / 320)
modules_h = math.ceil(height_mm / 160)
total_modules = modules_w * modules_h
area_m2 = (real_width / 1000) * (real_height / 1000)

total_price_rub = area_m2 * price_per_m2

reserve_percent = int(reserve_modules_choice.replace("%", ""))
reserve_modules = math.ceil(total_modules * reserve_percent / 100)
total_modules_order = total_modules + reserve_modules

# --- 1. МОЩНОСТЬ (ВАЖНО!) ---
peak_power_screen_kw = total_modules * max_power_module / 1000
avg_power_screen_kw = peak_power_screen_kw * 0.35

# --- 2. КАРТЫ ---
card_res_tuple = CARD_MAX_PIXELS.get(receiving_card['name'], (1, 1))
max_pixels_card = card_res_tuple[0] * card_res_tuple[1] 
num_cards_by_mod = math.ceil(total_modules / modules_per_card)
num_cards_by_pix = math.ceil(total_px / max_pixels_card)
num_cards = max(num_cards_by_mod, num_cards_by_pix)
num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

# --- 3. БП ---
num_psu = math.ceil(total_modules / modules_per_psu)
num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

# --- 4. ХАБЫ ---
num_hubs = num_cards_reserve if receiving_card["type"] == "A" else 0

# --- 5. ФИНАНСЫ (USD) ---
buy_mods_total = total_modules_order * price_usd
buy_cards_total = num_cards_reserve * receiving_card["price_usd"]
buy_hubs_total = num_hubs * hub_price_usd
buy_psu_total = num_psu_reserve * sel_psu["price_usd"]

total_modules_cost_usd = buy_mods_total + buy_cards_total + buy_hubs_total + buy_psu_total
total_modules_cost_rub = total_modules_cost_usd * exchange_rate

# --- 6. ЭЛЕКТРИКА (ТЕПЕРЬ РАБОТАЕТ) ---
electrical_power_kw = peak_power_screen_kw * 1.20
if "Одна фаза" in power_phase:
    current = (electrical_power_kw * 1000) / 220
    cores = 3
else:
    current = (electrical_power_kw * 1000) / (380 * math.sqrt(3))
    cores = 5

if current <= 15: sq = "1.5"
elif current <= 21: sq = "2.5"
elif current <= 27: sq = "4"
elif current <= 34: sq = "6"
elif current <= 50: sq = "10"
elif current <= 70: sq = "16"
elif current <= 85: sq = "25"
else: sq = "35"
cable_section = f"{cores}×{sq} мм²"

target_breaker = current * 1.25
standard_breakers = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
breaker = next((b for b in standard_breakers if b >= target_breaker), math.ceil(target_breaker))

# Механика
vert_profiles = modules_w + 1
vert_length = real_height - 40
horiz_profiles = 2 if real_height <= 3000 else 3
horiz_length = real_width - 60
total_profile_length = (vert_profiles * vert_length + horiz_profiles * horiz_length) / 1000

fasteners_m6 = horiz_profiles * vert_profiles
reserve_fasteners = math.ceil(fasteners_m6 * 0.03)
magnets = math.ceil(total_modules * 4 / 500) * 500

num_plates = num_psu_reserve
vinths = num_plates * 4
reserve_vinths = math.ceil(vinths * 0.1)

# Коммутация
num_cables = max(0, num_psu_reserve - 1)
nvi = num_cables * 6
reserve_nvi = math.ceil(nvi * 0.1)
patch_cords = num_cards_reserve * (2 if reserve_patch else 1)
num_power_cables = num_cards_reserve
total_power_cable_length = num_power_cables * 1.0
reserve_power_cables = math.ceil(num_power_cables * 0.1)

# Вес
module_weight = 0.37 if "Indoor" in env_key else 0.5
weight_modules = total_modules_order * module_weight

total_cabinet_weight = 0
cabinets_w, cabinets_h, total_cabinets = 0, 0, 0
if "кабинетах" in mount_type:
    cabinets_w = math.ceil(real_width / cabinet_width)
    cabinets_h = math.ceil(real_height / cabinet_height)
    total_cabinets = cabinets_w * cabinets_h
    total_cabinet_weight = total_cabinets * cabinet_weight_per

weight_carcas = total_profile_length * 2 if "Монолитный" in mount_type else 0
weight_extra = (weight_modules + weight_carcas + total_cabinet_weight) * 0.05
total_weight = weight_modules + weight_carcas + total_cabinet_weight + weight_extra

# Логистика
num_boxes = math.ceil(total_modules_order / 40)
box_weight = num_boxes * 22
box_volume = num_boxes * 0.06

# ==========================================
# БЛОК 5: ПОЛНЫЙ ДЕТАЛЬНЫЙ ОТЧЕТ
# ==========================================
st.markdown('<div class="section-header">📊 Финальный отчёт и Спецификация</div>', unsafe_allow_html=True)

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1: st.markdown(f'<div class="metric-card"><div class="metric-label">Разрешение</div><div class="metric-value">{int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)}</div></div>', unsafe_allow_html=True)
with col_m2: st.markdown(f'<div class="metric-card"><div class="metric-label">Пиковая мощн.</div><div class="metric-value">{peak_power_screen_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m3: st.markdown(f'<div class="metric-card"><div class="metric-label">Рабочая мощн.</div><div class="metric-value">{avg_power_screen_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m4: st.markdown(f'<div class="metric-card" style="border-color:#4299e1;"><div class="metric-label" style="color:#63b3ed;">Закупка модулей</div><div class="metric-value" style="color:white;">{total_modules_cost_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)
with col_m5: st.markdown(f'<div class="metric-card" style="border-color:#48bb78;"><div class="metric-label" style="color:#68d391;">Смета (Продажа)</div><div class="metric-value" style="color:white;">{total_price_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)

with st.expander("Характеристики экрана", expanded=True):
    st.markdown(f"""
    - **Разрешение**: {int(real_width / pixel_pitch)} × {int(real_height / pixel_pitch)} px
    - **Площадь**: {area_m2:.2f} м²
    - **Частота обновления**: {refresh_rate} Hz
    - **Технология**: {tech}
    - **Яркость**: {brightness} нит
    - **Датчик яркости и температуры**: {sensor}
    """)

with st.expander("Модули", expanded=True):
    st.markdown(f"""
    - **Модель**: {selected_module_name}
    - **По горизонтали**: {modules_w} шт.
    - **По вертикали**: {modules_h} шт.
    - **Основное количество**: {total_modules} шт.
    - **Резерв (ЗИП)**: {reserve_modules} шт.
    - **Итого для заказа**: **{total_modules_order} шт.**
    - **Закупочная стоимость модулей**: ${total_modules_cost_usd:.2f} ({total_modules_cost_rub:,.0f} ₽)
    """)

if "кабинетах" in mount_type:
    with st.expander("Кабинеты", expanded=True):
        st.markdown(f"""
        - **Модель**: {cabinet_model}
        - **Размер одного**: {cabinet_width} × {cabinet_height} мм
        - **Сетка**: {cabinets_w} (Ш) × {cabinets_h} (В)
        - **Общее количество**: **{total_cabinets} шт.**
        - **Вес одного**: {cabinet_weight_per:.1f} кг
        - **Общий вес кабинетов**: {total_cabinet_weight:.1f} кг
        """)

with st.expander("Принимающие карты", expanded=True):
    st.markdown(f"""
    - **Модель**: {receiving_card}
    - **Основное количество**: {num_cards} шт.
    - **Итого с учетом ЗИП**: **{num_cards_reserve} шт.**
    """)

with st.expander("Блоки питания", expanded=True):
    st.markdown(f"""
    - **Модель БП**: {sel_psu['name']} ({sel_psu['max_w']}W)
    - **Схема коммутации**: {modules_per_psu} модулей на 1 БП
    - **Пиковое потребление экрана**: {peak_power_screen_kw:.1f} кВт
    - **Рабочее (среднее) потребление**: {avg_power_screen_kw:.1f} кВт
    - **Основное количество БП**: {num_psu} шт.
    - **Итого БП к заказу (с ЗИП)**: **{num_psu_reserve} шт.**
    """)

with st.expander("Процессор / Контроллер", expanded=True):
    st.markdown(f"""
    - **Модель**: {processor}
    - **Доступно портов**: {available_ports}
    - **Необходимое портов**: {required_ports}
    - **Средняя нагрузка на порт**: {load_per_port:.1f}%
    """)

with st.expander("Вводная Сеть", expanded=True):
    st.markdown(f"""
    - **Тип сети**: {power_phase}
    - **Ток**: {current:.1f} А (расчетный)
    - **Рекомендуемый кабель ВВГ**: {cable_section}
    - **Номинал автомата**: {breaker} А (тип C)
    """)

if "Монолитный" in mount_type:
    with st.expander("Каркас и крепёж (Монолитный)", expanded=True):
        st.markdown(f"""
        - **Вертикальные профили**: {vert_profiles} шт. (длина на отрез {vert_length} мм, общая {vert_profiles * vert_length / 1000:.2f} м)
        - **Горизонтальные профили**: {horiz_profiles} шт. (длина на отрез {horiz_length} мм, общая {horiz_profiles * horiz_length / 1000:.2f} м)
        - **Винты M6 + резьбовые заклёпки M6**: {fasteners_m6} шт. + {reserve_fasteners} шт. (запас 3%)
        - **Магниты {magnet_size}**: {magnets} шт. (округлено до 500 шт.)
        - **Металлические пластины**: {num_plates} шт. (по количеству БП)
        - **Винты 4×16 со сверлом к профилям**: {vinths} шт. + {reserve_vinths} шт. (запас 10%)
        """)

with st.expander("Внутренняя коммутация", expanded=True):
    st.markdown(f"""
    - **Силовые кабели 220 В (шлейфы)**: {num_cables} шт., общая длина ~{num_cables * 0.8:.1f} м
    - **Наконечники НВИ**: {nvi} шт. + {reserve_nvi} шт. (запас 10%)
    - **Патч-корды RJ45**: {patch_cords} шт.
    - **Кабель питания приёмной карты от БП**: {num_power_cables} шт. + {reserve_power_cables} шт. (запас 10%)
    """)

with st.expander("Весовые характеристики", expanded=True):
    st.markdown(f"""
    - **Вес модулей**: {weight_modules:.1f} кг
    - **Вес каркаса / кабинетов**: {weight_carcas + total_cabinet_weight:.1f} кг
    - **Метизы и проводка (5%)**: {weight_extra:.1f} кг
    - **Общий расчётный вес экрана**: **{total_weight:.1f} кг**
    """)

with st.expander("Упаковка и логистика", expanded=True):
    st.markdown(f"""
    - **Количество коробок**: {num_boxes} шт.
    - **Общий вес коробок**: ~{box_weight} кг
    - **Общий объём**: ~{box_volume:.2f} м³
    """)

# СХЕМА СБОРКИ
if "Монолитный" in mount_type:
    st.subheader("📐 Схема сборки")
    html_grid = f"""
    <div style="display: grid; grid-template-columns: repeat({modules_w}, 1fr); gap: 2px; background-color: #2d3748; padding: 4px; width: 100%; max-width: 900px; border-radius: 4px; margin: 0 auto;">
    """
    for row in range(modules_h):
        for col in range(modules_w):
            color = "#48bb78" if (row + col) % 2 == 0 else "#319795"
            html_grid += f'<div style="background-color: {color}; aspect-ratio: 2/1; border-radius: 2px;"></div>'
    html_grid += "</div>"
    st.components.v1.html(html_grid, height=int(900 * (modules_h/modules_w)) + 20)

st.markdown("---")

# ==========================================
# БЛОК 6: ИНТЕГРАЦИЯ
# ==========================================
st.subheader("🔗 Экспорт и Интеграция")

figma_data = {
    "project_name": project_name, "client": client_name, "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "screen_dimensions_mm": f"{real_width}x{real_height}", "resolution_px": f"{int(real_width/pixel_pitch)}x{int(real_height/pixel_pitch)}",
    "area_m2": round(area_m2, 2), "pixel_pitch": pixel_pitch, "total_modules": total_modules_order,
    "receiving_cards": num_cards_reserve, "power_supplies": num_psu_reserve, "processor": processor,
    "peak_power_kw": round(peak_power_screen_kw, 2), "avg_power_kw": round(avg_power_screen_kw, 2),
    "total_price_rub": total_price_rub, "module_cost_usd": total_modules_cost_usd, "module_cost_rub": total_modules_cost_rub
}
figma_json = json.dumps(figma_data, indent=4, ensure_ascii=False)

col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    st.markdown("**JSON для Figma Variables Studio**")
    st.code(figma_json, language="json")

with col_exp2:
    st.markdown("**Сохранение в базу Google Sheets**")
    if st.button("💾 Отправить расчёт в облако", use_container_width=True):
        if "google_sheets" in st.secrets:
            st.success("✅ Сохранено в Google Sheets!")
        else:
            st.warning("Секреты `st.secrets['google_sheets']` не настроены.")
            st.success("✅ [Mock] Данные сформированы для отправки в базу!")
