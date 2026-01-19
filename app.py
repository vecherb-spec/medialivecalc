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
    st.session_state.height_mm = 2240

# Функции пересчёта
def fit_ratio(ratio):
    ideal = st.session_state.width_mm / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Ввод параметров
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип экрана")

    # Популярные размеры только 16:9 (ширина + рассчитанная высота)
    popular_16_9 = {
        "2560 × 1440": (2560, 1440),
        "3200 × 1800": (3200, 1800),
        "3840 × 2160": (3840, 2160),
        "4120 × 2340": (4120, 2340),
        "4800 × 2700": (4800, 2700),
        "5120 × 2880": (5120, 2880),
        "6080 × 3420": (6080, 3420),
        "Свой размер (вручную)": (None, None)
    }

    # Выпадающий список размеров
    selected_label = st.selectbox(
        "Выберите популярный размер 16:9",
        list(popular_16_9.keys()),
        index=2  # по умолчанию 3840×2160
    )

    # Если выбран готовый размер — подставляем ширину и высоту
    selected_w, selected_h = popular_16_9[selected_label]
    if selected_w is not None:
        st.session_state.width_mm = selected_w
        st.session_state.height_mm = selected_h
        st.rerun()  # обновляем страницу после выбора

    # Поле ширины (можно менять вручную)
    width_mm = st.number_input(
        "Ширина экрана (мм)",
        min_value=320,
        step=320,
        value=st.session_state.get("width_mm", 3840),
        key="width_input"
    )
    st.session_state["width_mm"] = width_mm

    # Кнопки подгонки в форме (все 4 пропорции)
    with st.form(key="ratio_form"):
        col16, col43, col21, col11 = st.columns(4)
        with col16:
            if st.form_submit_button("16:9", type="primary"):
                fit_ratio(1.7777777777777777)
                st.success(f"Высота подогнана под 16:9: {st.session_state.height_mm} мм")
                st.rerun()

        with col43:
            if st.form_submit_button("4:3", type="primary"):
                fit_ratio(1.3333333333333333)
                st.success(f"Высота подогнана под 4:3: {st.session_state.height_mm} мм")
                st.rerun()

        with col21:
            if st.form_submit_button("21:9", type="primary"):
                fit_ratio(2.3333333333333335)
                st.success(f"Высота подогнана под 21:9: {st.session_state.height_mm} мм")
                st.rerun()

        with col11:
            if st.form_submit_button("1:1", type="primary"):
                fit_ratio(1.0)
                st.success(f"Высота подогнана под 1:1: {st.session_state.height_mm} мм")
                st.rerun()

    # Поле высоты — без ключа, чтобы обновлялось визуально
    height_mm = st.number_input(
        "Высота экрана (мм)",
        min_value=160,
        step=160,
        value=st.session_state.get("height_mm", 2240)
    )
    st.session_state.height_mm = height_mm

    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)
