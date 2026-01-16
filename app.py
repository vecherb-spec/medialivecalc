import streamlit as st
import math

# ----------------- Конфигурация страницы -----------------
st.set_page_config(
    page_title="Калькулятор LED-экранов MediaLive",
    layout="wide",
    page_icon="🖥️"
)

# ----------------- Дизайн -----------------
st.markdown("""
<style>
.main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
.stButton>button {
    background: linear-gradient(90deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: bold;
    transition: all 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
}
.card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.1);
    margin: 15px 0;
}
h1, h2, h3 {color: #a78bfa !important;}
</style>
""", unsafe_allow_html=True)

st.title("🖥️ Калькулятор LED-экранов MediaLive")
st.markdown("Инженерный конфигуратор экранов Qiangli 320×160 мм")

# ----------------- Справочники -----------------
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

CARD_MAX_PIXELS = {
    "A5s Plus": 320*256, "A7s Plus": 512*256, "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512, "MRV412": 512*512,
    "MRV416": 512*384, "MRV432": 512*512, "MRV532": 512*512,
    "NV3210": 512*384, "MRV208-N / MRV208-1": 256*256,
    "MRV470-1": 512*384, "A4s Plus": 256*256
}

INDOOR_PITCHES = [0.8, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0, 6.66, 8.0, 10.0]

# ----------------- Ввод параметров -----------------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер экрана")
    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=2880)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"])

with col2:
    st.subheader("Монтаж и пиксель")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"])
    if screen_type == "Indoor":
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8)
    else:
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0)
    tech = st.selectbox("Технология", ["SMD", "COB", "GOB"])

with col3:
    st.subheader("Система управления")
    refresh_rate = st.selectbox("Частота обновления", [1920, 2880, 3840, 6000, 7680], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"])

    if system_type == "Синхронный":
        processors = ["VC2","VC4","VC6","VC10","VC16","VC24",
                      "MCTRL300","MCTRL600","MCTRL700","MCTRL4K","MCTRL R5",
                      "VX400","VX600 Pro","VX1000 Pro","VX2000 Pro","VX16S"]
    else:
        processors = ["TB10 Plus","TB30","TB40","TB50","TB60"]

    processor = st.selectbox("Процессор", processors)

# ----------------- Доп. параметры -----------------
receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()))
modules_per_card = st.selectbox("Модулей на карту", [8,10,12,16], index=0)
psu_power = st.selectbox("Мощность БП (Вт)", [200,300,400], index=0)
power_reserve = st.radio("Запас по питанию (%)", [15,30], index=1)
power_phase = st.radio("Сеть", ["Одна фаза (220 В)", "Три фазы (380 В)"])

reserve_enabled = st.checkbox("Добавить резерв", value=True)

# ----------------- Кнопка расчёта -----------------
if st.button("Рассчитать", type="primary", use_container_width=True):

    # Геометрия
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    # Разрешение
    total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)

    # Потребление
    avg_power = 8 if screen_type == "Indoor" else 15
    max_power = 24 if screen_type == "Indoor" else 45
    peak_power = total_modules * max_power / 1000
    power_with_reserve = peak_power * (1 + power_reserve/100)

    # БП
    num_psu = math.ceil(power_with_reserve / (psu_power/1000))

    # Карты
    max_pixels_card = CARD_MAX_PIXELS[receiving_card]
    num_cards = max(
        math.ceil(total_modules / modules_per_card),
        math.ceil(total_px / max_pixels_card)
    )

    # Сеть
    voltage = 220 if power_phase.startswith("Одна") else 380*math.sqrt(3)
    current = power_with_reserve * 1000 / voltage

    # Вес
    module_weight = 0.37 if screen_type == "Indoor" else 0.5
    total_weight = total_modules * module_weight

    # ----------------- Отчёт -----------------
    st.success("Расчёт выполнен")

    st.markdown("## 📊 Финальный отчёт")

    st.markdown(f"""
    ### Экран
    - Размер: {real_width} × {real_height} мм  
    - Разрешение: {int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)} px  
    - Площадь: {real_width*real_height/1_000_000:.2f} м²  
    - Модулей: {total_modules} шт  

    ### Электропитание
    - Пиковая мощность: {peak_power:.2f} кВт  
    - С запасом: {power_with_reserve:.2f} кВт  
    - Блоков питания: {num_psu} шт  

    ### Управление
    - Процессор: {processor}  
    - Принимающие карты: {num_cards} шт  

    ### Электросеть
    - Напряжение: {voltage:.0f} В  
    - Ток: {current:.1f} А  

    ### Вес
    - Общий вес: {total_weight:.1f} кг
    """)

