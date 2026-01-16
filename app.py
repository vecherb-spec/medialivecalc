import streamlit as st
import math

# Конфигурация страницы
st.set_page_config(page_title="MediaLive LED Calculator", layout="wide", page_icon="🖥️")

# Дизайн
st.markdown("""
    <style>
    .main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
    .stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border-radius: 12px; padding: 12px 24px; font-weight: bold;}
    .card {background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px;}
    h1, h2, h3 {color: #a78bfa !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ MediaLive LED Engineering Calculator")

# ============================
# Процессоры (реальные порты)
# ============================
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
    "MCTRL660 Pro": 6,
    "MCTRL700": 6,
    "MCTRL4K": 16,
    "MCTRL R5": 8,

    "TB10 Plus": 1,
    "TB30": 1,
    "TB40": 2,
    "TB50": 2,
    "TB60": 4
}

PORT_MAX_PIXELS = {k: 650000 for k in PROCESSOR_PORTS}

# ============================
# Приёмные карты
# ============================
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

# ============================
# Ввод данных
# ============================
col1, col2, col3 = st.columns(3)

with col1:
    width_mm = st.number_input("Ширина экрана (мм)", 320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", 160, step=160, value=2880)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"])

with col2:
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", [1.25,1.56,1.86,2.5,3.07,4,5,6.67])
    mount_type = st.radio("Тип монтажа", ["Монолитный", "В кабинетах"])

with col3:
    refresh_rate = st.selectbox("Частота обновления", [1920, 3840, 7680])
    system_type = st.radio("Тип системы", ["Synchronous", "Asynchronous"])

if system_type == "Synchronous":
    processor = st.selectbox("Процессор", [p for p in PROCESSOR_PORTS if not p.startswith("TB")])
else:
    processor = st.selectbox("Плеер", ["TB10 Plus","TB30","TB40","TB50","TB60"])

receiving_card = st.selectbox("Приёмная карта", list(CARD_MAX_PIXELS.keys()))
modules_per_card = st.selectbox("Модулей на карту", [8,10,12,16], index=2)

psu_power = st.selectbox("Мощность БП (Вт)", [200,300,400], index=2)
power_reserve = st.number_input("Запас по питанию (%)", value=30)

power_phase = st.radio("Сеть", ["Одна фаза (220 В)", "Три фазы (380 В)"])

reserve_modules_choice = st.radio("Резерв модулей", ["3%","5%","10%","Свой"])
reserve_modules_custom = 0
if reserve_modules_choice == "Свой":
    reserve_modules_custom = st.number_input("Резерв модулей (шт)", value=0)

# ============================
# Кнопка расчёта
# ============================
if st.button("Рассчитать", use_container_width=True):

    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    # Резерв модулей
    if reserve_modules_choice == "3%":
        reserve_modules_percent = 3
    elif reserve_modules_choice == "5%":
        reserve_modules_percent = 5
    elif reserve_modules_choice == "10%":
        reserve_modules_percent = 10

    reserve_modules = math.ceil(total_modules * reserve_modules_percent / 100) if reserve_modules_choice != "Свой" else reserve_modules_custom
    total_modules_order = total_modules + reserve_modules

    # Пиксели
    total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)

    # Карты
    max_pixels_card = CARD_MAX_PIXELS[receiving_card]
    cards_by_modules = math.ceil(total_modules / modules_per_card)
    cards_by_pixels = math.ceil(total_px / max_pixels_card)
    num_cards = max(cards_by_modules, cards_by_pixels)

    # Питание
    avg_power_module = 8 if screen_type == "Indoor" else 15
    max_power_module = 24 if screen_type == "Indoor" else 45
    peak_power_screen = total_modules * max_power_module / 1000
    power_with_reserve = peak_power_screen * (1 + power_reserve/100)

    num_psu = math.ceil(power_with_reserve / (psu_power/1000))

    # Ток
    if power_phase == "Одна фаза (220 В)":
        current = power_with_reserve * 1000 / 220
    else:
        current = power_with_reserve * 1000 / (math.sqrt(3) * 380)

    # Кабель
    if power_phase == "Одна фаза (220 В)":
        cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
    else:
        cable_section = "5×10 мм²" if current < 40 else "5×16 мм²" if current < 63 else "5×25 мм²"

    # Процессор
    available_ports = PROCESSOR_PORTS[processor]
    port_capacity = PORT_MAX_PIXELS[processor]
    required_ports = math.ceil(total_px / port_capacity)
    load_per_port = (total_px / (available_ports * port_capacity)) * 100

    # ============================
    # Отчёт
    # ============================
    st.success("Расчёт выполнен")

    st.subheader("Экран")
    st.markdown(f"""
    - Размер: {real_width} × {real_height} мм  
    - Разрешение: {int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)} px  
    - Площадь: {real_width*real_height/1_000_000:.2f} м²  
    """)

    st.subheader("Модули")
    st.markdown(f"""
    - По горизонтали: {modules_w}
    - По вертикали: {modules_h}
    - Основные: {total_modules}
    - Резерв: {reserve_modules}
    - Итого: {total_modules_order}
    """)

    st.subheader("Приёмные карты")
    st.markdown(f"""
    - Модель: {receiving_card}
    - Количество: {num_cards} шт
    """)

    st.subheader("Питание")
    st.markdown(f"""
    - Пиковая мощность: {peak_power_screen:.1f} кВт
    - С запасом: {power_with_reserve:.1f} кВт
    - Блоки питания: {num_psu} шт
    - Ток: {current:.1f} А
    - Кабель: {cable_section}
    """)

    st.subheader("Процессор")
    st.markdown(f"""
    - Модель: {processor}
    - Портов: {available_ports}
    - Требуется портов: {required_ports}
    - Нагрузка на порт: {load_per_port:.1f} %
    """)

    if required_ports > available_ports:
        st.error("❌ Процессор не справляется с данным разрешением!")

    if load_per_port > 80:
        st.warning("⚠ Нагрузка на порт превышает 80% — рекомендуется процессор классом выше.")
