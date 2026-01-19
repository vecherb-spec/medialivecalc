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
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ Калькулятор LED-экранов MediaLive")
st.markdown("Расчёт комплектующих для экранов Qiangli 320×160 мм — быстро и точно")

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

    # Популярные размеры только 16:9
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
        index=2  # по умолчанию 3840×2160
    )

    selected_w, selected_h = popular_16_9[selected_label]
    if selected_w is not None:
        st.session_state.width_mm = selected_w
        st.session_state.height_mm = selected_h

    width_mm = st.number_input(
        "Ширина экрана (мм)",
        min_value=320,
        step=320,
        value=st.session_state.get("width_mm", 3840),
        key="width_input"
    )
    st.session_state["width_mm"] = width_mm

    # Кнопки подгонки — рабочий вариант
    with st.form(key="ratio_form"):
        col16, col43 = st.columns(2)
        with col16:
            if st.form_submit_button("Подогнать под 16:9", type="primary"):
                fit_ratio(1.7777777777777777)
                st.success(f"Высота подогнана под 16:9: {st.session_state.height_mm} мм")
                st.rerun()

        with col43:
            if st.form_submit_button("Подогнать под 4:3", type="primary"):
                fit_ratio(1.3333333333333333)
                st.success(f"Высота подогнана под 4:3: {st.session_state.height_mm} мм")
                st.rerun()

    height_mm = st.number_input(
        "Высота экрана (мм)",
        min_value=160,
        step=160,
        value=st.session_state.get("height_mm", 2160)
    )
    st.session_state.height_mm = height_mm

    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

# Остальной код (монтаж, шаг, кабинеты, процессор, проверка портов, магнит, датчик, карта, ориентиры, БП, сеть, резерв, расчёт, отчёт, схема) — вставь сюда свой полный код
# Для теста оставь хотя бы это:
with col2:
    st.subheader("Тест")
    st.write("Если ты видишь это — приложение загрузилось!")

    if st.button("Рассчитать"):
        st.success("Расчёт готов!")
