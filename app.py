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
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 1, "MCTRL660 Pro": 2, "MCTRL700": 4, "MCTRL4K": 4, "MCTRL R5": 4,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

# Данные карт
CARD_MAX_PIXELS = {
    "A5s Plus": 320*256, "A7s Plus": 512*256, "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512, "MRV412": 512*512, "MRV416": 512*384,
    "MRV432": 512*512, "MRV532": 512*512, "NV3210": 512*384,
    "MRV208-N / MRV208-1": 256*256, "MRV470-1": 512*384, "A4s Plus": 256*256
}

# Ввод параметров
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип экрана")
    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=2880)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

with col2:
    st.subheader("Монтаж и шаг пикселя")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", [0.8,1.0,1.25,1.37,1.53,1.66,1.86,2.0,2.5,3.07,4.0,5.0,6.67,8.0,10.0], index=8)
    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

with col3:
    st.subheader("Частота и система")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920,2880,3840,6000,7680], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    if system_type == "Синхронный":
        available_processors = [p for p in PROCESSOR_PORTS if not p.startswith("TB")]
    else:
        available_processors = ["TB10 Plus","TB30","TB40","TB50","TB60"]

    processor = st.selectbox("Процессор/плеер", available_processors, index=0)

magnet_size = "13 мм"
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм","13 мм","17 мм"], index=1)

sensor = "Нет"
if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости и температуры", ["Нет","Есть (NSO60 или аналог)"], index=1)

receiving_card = st.selectbox("Принимающая карта (Novastar)", list(CARD_MAX_PIXELS.keys()), index=5)
modules_per_card = st.selectbox("Модулей на карту", [8,10,12,16], index=0)
modules_per_psu = st.selectbox("Модулей на БП", [4,6,8,10], index=2)
power_reserve = st.radio("Запас по питанию", [15,30], index=1)
psu_power = st.selectbox("Мощность БП (Вт)", [200,300,400], index=2)
power_phase = st.radio("Подключение к сети", ["Одна фаза (220 В)","Три фазы (380 В)"], index=0)

reserve_enabled = st.checkbox("Включить резервные элементы?", value=True)
reserve_modules_percent = 5
reserve_modules_custom = 0
reserve_psu_cards = False
reserve_patch = False

if reserve_enabled:
    reserve_modules_choice = st.radio("Резерв модулей", ["3%","5%","10%","Свой"], index=1)
    if reserve_modules_choice == "Свой":
        reserve_modules_custom = st.number_input("Свой резерв модулей (шт.)", value=0)
    reserve_psu_cards = st.checkbox("+1 к БП и картам", value=True)
    reserve_patch = st.checkbox("Резервные патч-корды (×2)", value=False)

if st.button("Рассчитать", type="primary", use_container_width=True):

    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    reserve_modules = math.ceil(total_modules * reserve_modules_percent / 100) if reserve_modules_choice != "Свой" else reserve_modules_custom
    total_modules_order = total_modules + reserve_modules

    avg_power_module = 8.0 if screen_type == "Indoor" else 15.0
    max_power_module = 24.0 if screen_type == "Indoor" else 45.0
    peak_power_screen = total_modules * max_power_module / 1000
    power_with_reserve = peak_power_screen * (1 + power_reserve / 100)

    psu_power_kw = psu_power / 1000
    num_psu = math.ceil(power_with_reserve / psu_power_kw)
    num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

    max_pixels_card = CARD_MAX_PIXELS[receiving_card]
    total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)
    num_cards = math.ceil(total_px / max_pixels_card)
    num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

    voltage = 220 if power_phase == "Одна фаза (220 В)" else 380 * math.sqrt(3)
    current = power_with_reserve * 1000 / voltage
    cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
    breaker = math.ceil(current * 1.25)

    st.success("Расчёт готов!")

    with st.expander("Процессор и порты", expanded=True):
        st.markdown(
            f"""
- **Модель**: {processor}
- **Всего пикселей**: {int(total_px):,}
- **Портов у процессора**: {PROCESSOR_PORTS.get(processor,1)}
- **Требуется портов**: {math.ceil(total_px / 650000)}
- **Нагрузка на порт**: {(total_px / (PROCESSOR_PORTS.get(processor,1)*650000))*100:.1f} %
"""
        )

    with st.expander("Сеть", expanded=True):
        st.markdown(
            f"""
- **Тип**: {power_phase}
- **Ток**: {current:.1f} А
- **Кабель**: {cable_section}
- **Автомат**: {breaker} А
"""
        )

    with st.expander("Модули", expanded=True):
        st.markdown(
            f"""
- По горизонтали: {modules_w}
- По вертикали: {modules_h}
- Основные: {total_modules}
- Резерв: {reserve_modules}
- Итого: {total_modules_order}
"""
        )

    with st.expander("Блоки питания", expanded=True):
        st.markdown(
            f"""
- Мощность БП: {psu_power} Вт
- Пиковая мощность экрана: {peak_power_screen:.1f} кВт
- С запасом: {power_with_reserve:.1f} кВт
- Количество БП: {num_psu_reserve} шт.
"""
        )

    with st.expander("Принимающие карты", expanded=True):
        st.markdown(
            f"""
- Модель: {receiving_card}
- Количество: {num_cards_reserve} шт.
"""
        )
