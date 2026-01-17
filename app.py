import streamlit as st
import math

st.set_page_config(page_title="Калькулятор LED-экранов MediaLive", layout="wide", page_icon="🖥️")

st.markdown("""
    <style>
    .main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
    .stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; padding: 12px 24px; font-weight: bold;}
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

# Функция пересчёта
def update_height():
    ideal = st.session_state.width_mm / 1.7777777777777777
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Блок размеров + кнопка автоподбора
col1, col2 = st.columns([4, 1])

with col1:
    st.subheader("Размер экрана")
    st.session_state.width_mm = st.number_input(
        "Ширина (мм)",
        min_value=320,
        step=320,
        value=st.session_state.width_mm,
        key="width_input"
    )

with col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # выравнивание кнопки
    with st.form(key="autofit"):
        if st.form_submit_button("Автоподбор 16:9", type="primary", use_container_width=True):
            update_height()
            st.rerun()

# Поле высоты
st.number_input(
    "Высота (мм)",
    min_value=160,
    step=160,
    value=st.session_state.height_mm,
    key="height_input"
)

# Остальной твой код идёт дальше (тип экрана, монтаж, шаг, кабинеты, процессор и т.д.)
# Вставь сюда весь остальной интерфейс и расчёты из твоего оригинального файла
