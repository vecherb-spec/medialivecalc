import streamlit as st
import math

st.set_page_config(page_title="LED Калькулятор", layout="wide")

st.title("Калькулятор LED-экранов")

# Сессионное состояние
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Размер экрана")

    width_mm = st.number_input("Ширина (мм)", min_value=320, step=320, value=st.session_state.width_mm)
    st.session_state.width_mm = width_mm

    # Кнопки подгонки (в форме — стабильный способ)
    with st.form(key="ratio_form"):
        if st.form_submit_button("Подогнать под 16:9"):
            ideal = width_mm / 1.7777777777777777
            new_h = round(ideal / 160) * 160
            st.session_state.height_mm = max(160, new_h)
            st.success(f"Высота подогнана под 16:9: {st.session_state.height_mm} мм")
            st.rerun()

        if st.form_submit_button("Подогнать под 4:3"):
            ideal = width_mm / 1.3333333333333333
            new_h = round(ideal / 160) * 160
            st.session_state.height_mm = max(160, new_h)
            st.success(f"Высота подогнана под 4:3: {st.session_state.height_mm} мм")
            st.rerun()

    # Поле высоты — без ключа, чтобы обновлялось визуально
    height_mm = st.number_input("Высота (мм)", min_value=160, step=160, value=st.session_state.height_mm)
    st.session_state.height_mm = height_mm

with col2:
    st.write("Здесь будет остальной интерфейс (монтаж, шаг пикселя, расчёт и т.д.)")

    # Пример кнопки расчёта
    if st.button("Рассчитать"):
        st.success("Расчёт готов!")
        st.write(f"Ширина: {width_mm} мм")
        st.write(f"Высота: {height_mm} мм")
