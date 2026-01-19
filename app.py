import streamlit as st
import math

# Конфигурация страницы (без изменений)
st.set_page_config(page_title="Калькулятор LED-экранов MediaLive", layout="wide", page_icon="🖥️")


# Стили (без изменений)
st.markdown("""
    <style>
    .main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
    .stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; padding: 12px 24px; font-weight: bold; transition: all 0.3s;}
    .stButton>button:hover {transform: scale(1.05); box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);}
    </style>
""", unsafe_allow_html=True)


st.title("🖥️ Калькулятор LED-экранов MediaLive")
st.markdown("Расчёт комплектующих для экранов Qiangli 320×160 мм — быстро и точно")

# Инициализация session_state (только один раз)
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240


def fit_ratio(ratio):
    ideal = st.session_state.width_mm / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper


col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип экрана")

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

    selected_label = st.selectbox(
        "Выберите популярный размер 16:9",
        list(popular_16_9.keys()),
        index=2,
        key="size_select"  # Явный ключ
    )

    selected_w, selected_h = popular_16_9[selected_label]
    if selected_w is not None:
        st.session_state.width_mm = selected_w
        st.session_state.height_mm = selected_h

    # Ввод ширины с явным ключом
    width_mm = st.number_input(
        "Ширина экрана (мм)",
        min_value=320,
        step=320,
        value=st.session_state.width_mm,
        key="width_input"
    )
    st.session_state.width_mm = width_mm  # Обновляем только здесь

    # Кнопки подгонки (вне формы, без rerun)
    col_ratios = st.columns(4)
    with col_ratios[0]:
        if st.button("16:9", type="primary", key="ratio_16_9"):
            fit_ratio(16/9)
            st.info(f"Высота: {st.session_state.height_mm} мм (16:9)")

    with col_ratios[1]:
        if st.button("4:3", type="primary", key="ratio_4_3"):
            fit_ratio(4/3)
            st.info(f"Высота: {st.session_state.height_mm} мм (4:3)")

    with col_ratios[2]:
        if st.button("21:9", type="primary", key="ratio_21_9"):
            fit_ratio(21/9)
            st.info(f"Высота: {st.session_state.height_mm} мм (21:9)")

    with col_ratios[3]:
        if st.button("1:1", type="primary", key="ratio_1_1"):
            fit_ratio(1)
            st.info(f"Высота: {st.session_state.height_mm} мм (1:1)")

    # Ввод высоты с явным ключом
    height_mm = st.number_input(
        "Высота экрана (мм)",
        min_value=160,
        step=160,
        value=st.session_state.height_mm,
        key="heightinput"
    )
    st.session_state.height_mm = height_mm

    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0, key="screen_type")
# Остальной код (монтаж, шаг, кабинеты, процессор, проверка портов, магнит, датчик, карта, ориентиры, БП, сеть, резерв, расчёт, отчёт, схема)
with col2:
    st.subheader("Монтаж и шаг пикселя")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)

    if screen_type == "Indoor":
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8)
    else:
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0)

    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

    # Выбор кабинета (упрощённо, чтобы не ломать)
    st.write("Выбор кабинета (вставь свой код здесь)")

with col3:
    st.subheader("Частота и система")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    processor = st.selectbox("Процессор/плеер", ["Пример процессора"], index=0)

    # Проверка портов (упрощённо)
    st.write("Проверка портов (вставь свой код здесь)")

# Кнопка расчёта
if st.button("Рассчитать", type="primary", use_container_width=True):
    st.success("Расчёт готов!")
    st.write("Ширина:", width_mm, "мм")
    st.write("Высота:", height_mm, "мм")
    # Вставь сюда свой полный расчёт и отчёт
