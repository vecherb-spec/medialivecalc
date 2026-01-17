import streamlit as st
import math

# Конфигурация страницы
st.set_page_config(page_title="Калькулятор LED-экранов MediaLive", layout="wide", page_icon="🖥️")

# Красивый дизайн 2025 года
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #f0f4ff;
    }

    .stApp {
        background: transparent;
    }

    .stButton>button {
        background: linear-gradient(90deg, #7f5af0, #5e45d4);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.4s ease;
        box-shadow: 0 4px 15px rgba(127, 90, 240, 0.4);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(127, 90, 240, 0.6);
    }

    .card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: all 0.4s ease;
        margin: 16px 0;
    }

    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 40px rgba(127, 90, 240, 0.3);
    }

    h1, h2, h3 {
        color: #c084fc;
        text-shadow: 0 2px 10px rgba(192, 132, 252, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ Калькулятор LED-экранов MediaLive 2025")
st.markdown("Профессиональный расчёт экранов Qiangli 320×160 мм")

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

# Сессионное состояние для синхронизации ширины и высоты
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2880

# Функция для автоматического подбора высоты по 16:9 (кратно 160 мм)
def update_height_from_width():
    # Идеальная высота по 16:9
    ideal_height = (st.session_state.width_mm * 9) / 16
    # Округляем до ближайшего кратного 160
    new_height = round(ideal_height / 160) * 160
    st.session_state.height_mm = new_height

# Ввод параметров (в красивых карточках)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Размер и тип")
        width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=st.session_state.width_mm, key="width_input")
        st.session_state.width_mm = width_mm  # обновляем состояние

        # Автоматическое обновление высоты при изменении ширины
        if width_mm != st.session_state.width_mm:
            update_height_from_width()

        height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=st.session_state.height_mm, key="height_input")
        st.session_state.height_mm = height_mm

        screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

    with col2:
        st.subheader("Монтаж и шаг")
        mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)

        if screen_type == "Indoor":
            pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8)
        else:
            pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0)

        tech = st.selectbox("Технология", ["SMD", "COB", "GOB"], index=0)

    with col3:
        st.subheader("Частота и система")
        refresh_rate = st.selectbox("Частота (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)
        system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

        if system_type == "Синхронный":
            vc_processors = ["VC2", "VC4", "VC6", "VC10", "VC16", "VC24"]
            mctrl_processors = ["MCTRL300", "MCTRL600", "MCTRL700", "MCTRL4K", "MCTRL R5"]
            vx_processors = ["VX400", "VX600 Pro", "VX1000 Pro", "VX2000 Pro", "VX16S"]
            available_processors = vc_processors + mctrl_processors + vx_processors
        else:
            available_processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]
        processor = st.selectbox("Процессор", available_processors, index=0)

    st.markdown('</div>', unsafe_allow_html=True)

# Остальные поля и расчёты (как раньше)
# ... (вставь сюда все остальные поля: магнит, датчик, карта, ориентиры, запас, БП, сеть, резерв)

# Кнопка расчёта и отчёт (как раньше)
if st.button("Рассчитать", type="primary", use_container_width=True):
    # ... (твой полный блок расчётов и вывода отчёта остаётся без изменений)
    pass  # Замени на свой полный расчёт
