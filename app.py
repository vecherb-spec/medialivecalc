import streamlit as st
import math
import json
import datetime
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
    .metric-value { font-size: 28px; font-weight: bold; color: #63b3ed; }
    .metric-label { font-size: 14px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; }
    
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

# --- СПРАВОЧНИКИ ---
INDOOR_PITCHES = [0.8, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0, 6.66, 8.0, 10.0]

PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

CARD_MAX_PIXELS = {
    "A5s Plus": 320*256, "A7s Plus": 512*256, "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512, "MRV412": 512*512, "MRV416": 512*384,
    "MRV432": 512*512, "MRV532": 512*512, "NV3210": 512*384,
    "MRV208-N / MRV208-1": 256*256, "MRV470-1": 512*384, "A4s Plus": 256*256
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
price_per_m2 = st.sidebar.number_input("Цена за м² (₽)", min_value=0, value=150000, step=5000)

st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Точный расчет комплектующих для экранов Qiangli, Novastar и Mean Well.")

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
    screen_type = st.radio("Среда использования", ["Indoor (Внутренний)", "Outdoor (Уличный)"], horizontal=True)
    env_key = "Indoor" if "Indoor" in screen_type else "Outdoor"
    
    col_mat_1, col_mat_2 = st.columns(2)
    with col_mat_1:
        pitch_options = INDOOR_PITCHES if env_key == "Indoor" else OUTDOOR_PITCHES
        default_pitch_idx = 8 if env_key == "Indoor" else 0
        pixel_pitch = st.selectbox("Шаг пикселя (P)", pitch_options, index=default_pitch_idx)
    with col_mat_2:
        tech = st.selectbox("Технология", ["SMD", "COB", "GOB"], index=0)
        
    c_sens, c_bright = st.columns(2)
    with c_sens:
        sensor = "Нет"
        if env_key == "Outdoor":
            sensor = st.selectbox("Датчик яркости", ["Нет", "Есть (NS060)"], index=1)
    with c_bright:
        # ДОБАВЛЕН ВЫБОР ЯРКОСТИ
        if env_key == "Indoor":
            brightness = st.selectbox("Яркость (нит)", [600, 800, 1000, 1200, 1500], index=1) # 800 по умолчанию
        else:
            brightness = st.selectbox("Яркость (нит)", [4500, 5500, 6000, 6500, 8000, 10000], index=3) # 6500 по умолчанию

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
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)

with col_ctrl2:
    receiving_card = st.selectbox("Приёмная карта (Receiving Card)", list(CARD_MAX_PIXELS.keys()), index=5)
    modules_per_card = st.selectbox("Схема коммутации (Модулей на 1 карту)", [8, 10, 12, 16], index=0)

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
# БЛОК 4: ПИТАНИЕ И РЕЗЕРВ (ЗИП)
# ==========================================
st.markdown('<div class="section-header">⚡ 4. Питание сети и ЗИП</div>', unsafe_allow_html=True)

col_pwr, col_zip = st.columns(2)

with col_pwr:
    cc1, cc2 = st.columns(2)
    with cc1: psu_power = st.selectbox("Мощность БП", [200, 300, 400], format_func=lambda x: f"{x}W", index=0)
    with cc2: modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10, 12, 16], index=2)
    power_phase = st.radio("Вводная сеть", ["Одна фаза (220 В)", "Три фазы (380 В)"], horizontal=True, index=0)

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
# ПОЛНЫЕ ИНЖЕНЕРНЫЕ ВЫЧИСЛЕНИЯ
# ==========================================
modules_w = math.ceil(width_mm / 320)
modules_h = math.ceil(height_mm / 160)
total_modules = modules_w * modules_h
area_m2 = (real_width / 1000) * (real_height / 1000)
total_price_rub = area_m2 * price_per_m2

if reserve_modules_choice != "Свой":
    reserve_percent = int(reserve_modules_choice.replace("%", ""))
    reserve_modules = math.ceil(total_modules * reserve_percent / 100)
else:
    reserve_modules = reserve_modules_custom
total_modules_order = total_modules + reserve_modules

# Мощности
max_power_module = 24.0 if "Indoor" in env_key else 45.0
peak_power_screen_kw = total_modules * max_power_module / 1000
avg_power_screen_kw = peak_power_screen_kw * 0.35 # Рабочая (средняя) мощность ~35%

# Расчет БП ТОЛЬКО по количеству хвостов (модулей на БП)
num_psu = math.ceil(total_modules / modules_per_psu)
num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

# Расчет принимающих карт
max_pixels_card = CARD_MAX_PIXELS[receiving_card]
num_cards_by_mod = math.ceil(total_modules / modules_per_card)
num_cards_by_pix = math.ceil(total_px / max_pixels_card)
num_cards = max(num_cards_by_mod, num_cards_by_pix)
num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

# Электрика (для автомата и кабеля всё еще считаем пиковую мощность, +20% скрытого запаса на пусковые токи)
electrical_power_kw = peak_power_screen_kw * 1.20 
voltage = 220 if "Одна фаза" in power_phase else 380 * math.sqrt(3)
current = electrical_power_kw * 1000 / voltage
cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
breaker = math.ceil(current * 1.25)

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

# 5 Колонок с показателями
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1: st.markdown(f'<div class="metric-card"><div class="metric-label">Площадь</div><div class="metric-value">{area_m2:.2f} м²</div></div>', unsafe_allow_html=True)
with col_m2: st.markdown(f'<div class="metric-card"><div class="metric-label">Разрешение</div><div class="metric-value">{int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)}</div></div>', unsafe_allow_html=True)
with col_m3: st.markdown(f'<div class="metric-card"><div class="metric-label">Пиковая мощн.</div><div class="metric-value">{peak_power_screen_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m4: st.markdown(f'<div class="metric-card"><div class="metric-label">Рабочая мощн.</div><div class="metric-value">{avg_power_screen_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m5: st.markdown(f'<div class="metric-card"><div class="metric-label">Смета (Прайс)</div><div class="metric-value">{total_price_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)

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
    - **По горизонтали**: {modules_w} шт.
    - **По вертикали**: {modules_h} шт.
    - **Основное количество**: {total_modules} шт.
    - **Резерв (ЗИП)**: {reserve_modules} шт.
    - **Итого для заказа**: **{total_modules_order} шт.**
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
    - **Модель БП**: {psu_power}W
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
    - **Ток**: {current:.1f} А (с учетом пусковых запасов)
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
    "total_price_rub": total_price_rub
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
