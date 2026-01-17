import streamlit as st
import math

# Конфигурация страницы
st.set_page_config(page_title="Калькулятор LED-экранов MediaLive", layout="wide", page_icon="🖥️")

# Красивый дизайн
st.markdown("""
    <style>
    .main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
    .stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; padding: 12px 24px; font-weight: bold; transition: all 0.3s;}
    .stButton>button:hover {transform: scale(1.05); box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);}
    .card {background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); margin: 15px 0;}
    h1, h2, h3 {color: #a78bfa !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ Калькулятор LED-экранов MediaLive")
st.markdown("Расчёт комплектующих для экранов Qiangli 320×160 мм — быстро и точно")

# Данные процессоров и портов
PROCESSOR_PORTS = {
    "VX400": 4,
    "VX600 Pro": 6,
    "VX1000 Pro": 10,
    "VX2000 Pro": 20,
    "VX16S": 16,
    "VC2": 2,
    "VC4": 4,
    "VC6": 6,
    "VC10": 10,
    "VC16": 16,
    "VC24": 24,
    "MCTRL300": 2,
    "MCTRL600": 4,
    "MCTRL700": 6,
    "MCTRL4K": 16,
    "MCTRL R5": 8,
    "TB10 Plus": 1,
    "TB30": 1,
    "TB40": 2,
    "TB50": 2,
    "TB60": 4
}

# Данные карт (max пикселей)
CARD_MAX_PIXELS = {
    "A5s Plus": 320*256,
    "A7s Plus": 512*256,
    "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512,
    "MRV412": 512*512,
    "MRV416": 512*384,
    "MRV432": 512*512,
    "MRV532": 512*512,
    "NV3210": 512*384,
    "MRV208-N / MRV208-1": 256*256,
    "MRV470-1": 512*384,
    "A4s Plus": 256*256
}

# Шаги пикселя по типу экрана
INDOOR_PITCHES = [0.8, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0, 6.66, 8.0, 10.0]

# Сессионное состояние
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240  # ближайшее к 2160.11

# Функция пересчёта высоты по 16:9 (кратно 160 мм)
def update_height():
    ideal = st.session_state.width_mm / 1.7777777777777777
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Ввод параметров
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип экрана")
    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=st.session_state.width_mm, key="width_input")
    st.session_state.width_mm = width_mm

    # Кнопка автоподбора — работает стабильно
    if st.button("Автоподбор 16:9", key="autofit_button"):
        update_height()
        st.rerun()

    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=st.session_state.height_mm, key="height_input")
    st.session_state.height_mm = height_mm

    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

with col2:
    st.subheader("Монтаж и шаг пикселя")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)

    if screen_type == "Indoor":
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8)
    else:
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0)

    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

    # Выбор кабинета
    cabinet_model = None
    cabinet_width = 640
    cabinet_height = 480
    cabinet_weight_per = 20.0
    if mount_type == "В кабинетах":
        st.subheader("Выбор кабинета Qiangli")
        cabinet_options = [
            "QM Series (640×480 мм, indoor, ~20 кг)",
            "MG Series (960×960 мм, outdoor/indoor, ~40 кг)",
            "QF Series (500×500 мм, rental/indoor, ~13.5 кг)",
            "QS Series (960×960 мм, outdoor fixed, ~45 кг)",
            "Custom (введите размер и вес вручную)"
        ]
        cabinet_model = st.selectbox("Модель кабинета", cabinet_options, index=0)

        cabinet_data = {
            "QM Series (640×480 мм, indoor, ~20 кг)": (640, 480, 20.0),
            "MG Series (960×960 мм, outdoor/indoor, ~40 кг)": (960, 960, 40.0),
            "QF Series (500×500 мм, rental/indoor, ~13.5 кг)": (500, 500, 13.5),
            "QS Series (960×960 мм, outdoor fixed, ~45 кг)": (960, 960, 45.0),
            "Custom (введите размер и вес вручную)": (None, None, None)
        }
        selected_data = cabinet_data.get(cabinet_model)
        if selected_data[0] is None:
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                cabinet_width = st.number_input("Ширина кабинета (мм)", min_value=320, value=640)
            with col_c2:
                cabinet_height = st.number_input("Высота кабинета (мм)", min_value=160, value=480)
            with col_c3:
                cabinet_weight_per = st.number_input("Вес одного кабинета (кг)", min_value=1.0, value=20.0, step=0.5)
        else:
            cabinet_width, cabinet_height, cabinet_weight_per = selected_data

with col3:
    st.subheader("Частота и система")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    if system_type == "Синхронный":
        available_processors = ["VC2", "VC4", "VC6", "VC10", "VC16", "VC24", "MCTRL300", "MCTRL600", "MCTRL700", "MCTRL4K", "MCTRL R5", "VX400", "VX600 Pro", "VX1000 Pro", "VX2000 Pro", "VX16S"]
    else:
        available_processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]
    processor = st.selectbox("Процессор/плеер", available_processors, index=0)

    # Проверка портов
    real_width = math.ceil(width_mm / 320) * 320
    real_height = math.ceil(height_mm / 160) * 160
    total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)
    required_ports = math.ceil(total_px / 650000)
    available_ports = PROCESSOR_PORTS.get(processor, 1)
    load_per_port = (total_px / (available_ports * 650000)) * 100 if available_ports > 0 else 100.0

    status_text = "Портов хватает" if required_ports <= available_ports else "Недостаточно портов!"
    status_color = "green" if required_ports <= available_ports else "red"

    st.markdown(f"""
    <div style="padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05); margin-top: 10px;">
        <strong>Проверка портов:</strong><br>
        Доступно: <strong>{available_ports}</strong><br>
        Нужно: <strong>{required_ports}</strong><br>
        Нагрузка: <strong>{load_per_port:.1f}%</strong><br>
        <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)

    if load_per_port > 90 and required_ports <= available_ports:
        st.warning("⚠️ Нагрузка >90%! Рекомендуем процессор помощнее.")

# Магнит, датчик, карта, ориентиры, запас, БП, сеть, резерв — всё на месте
magnet_size = "13 мм"
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

sensor = "Нет"
if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости и температуры", ["Нет", "Есть (NSO60 или аналог)"], index=1)

receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()), index=5)

modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)
modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10], index=2)

power_reserve = st.radio("Запас по питанию", [15, 30], index=1)

psu_power = st.selectbox("Мощность БП (Вт)", [200, 300, 400], index=0)

power_phase = st.radio("Подключение к сети", ["Одна фаза (220 В)", "Три фазы (380 В)"], index=0)

reserve_enabled = st.checkbox("Включить резерв?", value=True)
reserve_modules_percent = 5
reserve_modules_custom = 0
reserve_modules_choice = "5%"
reserve_psu_cards = False
reserve_patch = False
if reserve_enabled:
    reserve_modules_choice = st.radio("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1)
    if reserve_modules_choice == "Свой":
        reserve_modules_custom = st.number_input("Свой резерв модулей (шт.)", min_value=0)
    reserve_psu_cards = st.checkbox("+1 к БП и картам", value=True)
    reserve_patch = st.checkbox("Резерв патч-кордов ×2", value=False)

# Кнопка расчёта и весь расчёт + отчёт (как раньше)
if st.button("Рассчитать", type="primary", use_container_width=True):
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    reserve_modules = math.ceil(total_modules * reserve_modules_percent / 100) if reserve_modules_choice != "Свой" else reserve_modules_custom
    total_modules_order = total_modules + reserve_modules

    # ... (весь твой расчёт: потребление, БП, карты, пластины, винты, кабели, сеть, каркас, крепёж, коммутация, вес, упаковка, кабинеты — вставь сюда свой полный блок расчётов из предыдущей версии)

    st.success("Расчёт готов!")
    st.markdown("### Финальный отчёт")

    # ... (весь твой вывод отчёта с expander'ами: характеристики, модули, кабинеты, карты, БП, процессор, сеть, каркас, коммутация, вес, упаковка)

    if mount_type == "Монолитный":
        st.subheader("Схема монтажа")
        # ... (твой HTML-код схемы)
