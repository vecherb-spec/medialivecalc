import streamlit as st
import math
from datetime import datetime

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

# Константы
INDOOR_PITCHES = [0.8, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0, 6.66, 8.0, 10.0]

PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

CARD_MAX_PIXELS = {
    "A5s Plus": 320*256, "A7s Plus": 512*256, "A8s / A8s-N": 512*384,
    "A10s Plus-N / A10s Pro": 512*512, "MRV412": 512*512, "MRV416": 512*384,
    "MRV432": 512*512, "MRV532": 512*512, "NV3210": 512*384,
    "MRV208-N / MRV208-1": 256*256, "MRV470-1": 512*384, "A4s Plus": 256*256
}

# Сессионное состояние
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240
if "previous_selected" not in st.session_state:
    st.session_state.previous_selected = "3840 × 2160"

# Функция пересчёта
def fit_ratio(ratio):
    ideal = st.session_state.width_mm / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Ввод параметров
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип экрана")

    # Список популярных размеров
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
        index=2
    )

    # Подставляем размеры при изменении выбора
    if selected_label != st.session_state.previous_selected:
        selected_w, selected_h = popular_16_9[selected_label]
        if selected_w is not None:
            st.session_state.width_mm = selected_w
            st.session_state.height_mm = selected_h
        st.session_state.previous_selected = selected_label
        st.rerun()

    width_mm = st.number_input(
        "Ширина экрана (мм)",
        min_value=320,
        step=320,
        value=st.session_state.get("width_mm", 3840),
        key="width_input"
    )
    st.session_state.width_mm = width_mm

    # 4 кнопки подгонки
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

    height_mm = st.number_input(
        "Высота экрана (мм)",
        min_value=160,
        step=160,
        value=st.session_state.get("height_mm", 2240)
    )
    st.session_state.height_mm = height_mm

    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

# Монтаж и шаг пикселя
with col2:
    st.subheader("Монтаж и шаг пикселя")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)

    if screen_type == "Indoor":
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8)
    else:
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0)

    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

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

# Магнит, датчик, карта, ориентиры, БП, сеть, резерв
magnet_size = "13 мм"
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

sensor = "Нет"
if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости и температуры", ["Нет", "Есть (NSO60 или аналог)"], index=1)

receiving_card = st.selectbox("Принимающая карта (Novastar)", list(CARD_MAX_PIXELS.keys()), index=5)

modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)
modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10], index=2)

power_reserve = st.radio(
    "Запас по питанию",
    options=[0, 10, 20, 30],
    format_func=lambda x: f"{x}%",
    index=2
)

psu_power = st.selectbox(
    "Мощность БП",
    options=[200, 300, 400],
    format_func=lambda x: f"{x}W",
    index=0
)

power_phase = st.radio("Подключение к сети", ["Одна фаза (220 В)", "Три фазы (380 В)"], index=0)

reserve_enabled = st.checkbox("Включить резервные элементы?", value=True)
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
    reserve_patch = st.checkbox("Резервные патч-корды (×2)", value=False)

# Автоматический расчёт
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
num_cards = math.ceil(total_modules / modules_per_card)
total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)
num_cards_pix = math.ceil(total_px / max_pixels_card)
num_cards = max(num_cards, num_cards_pix)
num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

# Пластины = кол-во БП
num_plates = num_psu_reserve

# Винты к профилям
vinths = num_plates * 4
reserve_vinths = math.ceil(vinths * 0.1)

# Кабель питания карт от БП
num_power_cables = num_cards_reserve
total_power_cable_length = num_power_cables * 1.0
reserve_power_cables = math.ceil(num_power_cables * 0.1)

# Расчёт сети
if power_phase == "Одна фаза (220 В)":
    voltage = 220
else:
    voltage = 380 * math.sqrt(3)
current = power_with_reserve * 1000 / voltage
cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
breaker = math.ceil(current * 1.25)

# Каркас
vert_profiles = modules_w + 1
vert_length = real_height - 40
horiz_profiles = 2 if real_height <= 3000 else 3
horiz_length = real_width - 60
total_profile_length = (vert_profiles * vert_length + horiz_profiles * horiz_length) / 1000

# Крепёж
fasteners_m6 = horiz_profiles * vert_profiles
reserve_fasteners = math.ceil(fasteners_m6 * 0.03)
magnets = math.ceil(total_modules * 4 / 500) * 500

# Коммутация
num_cables = num_psu_reserve - 1
nvi = num_cables * 6
reserve_nvi = math.ceil(nvi * 0.1)
patch_cords = num_cards_reserve * (2 if reserve_patch else 1)

# Вес
module_weight = 0.37 if screen_type == "Indoor" else 0.5
weight_modules = total_modules_order * module_weight
weight_carcas = total_profile_length * 2 if mount_type == "Монолитный" else 0
weight_extra = (weight_modules + weight_carcas) * 0.05
total_weight = weight_modules + weight_carcas + weight_extra

# Упаковка
num_boxes = math.ceil(total_modules_order / 40)
box_weight = num_boxes * 22
box_volume = num_boxes * 0.06

# Кабинеты
total_cabinets = 0
total_cabinet_weight = 0.0
if mount_type == "В кабинетах":
    cabinets_w = math.ceil(real_width / cabinet_width)
    cabinets_h = math.ceil(real_height / cabinet_height)
    total_cabinets = cabinets_w * cabinets_h
    total_cabinet_weight = total_cabinets * cabinet_weight_per

# Вывод отчёта
st.success("Расчёт готов!")
st.markdown("### Финальный отчёт")

with st.expander("Характеристики экрана", expanded=True):
    st.markdown(f"""
    - **Разрешение**: {math.floor(real_width / pixel_pitch)} × {math.floor(real_height / pixel_pitch)} px
    - **Площадь**: {real_width * real_height / 1_000_000:.2f} м²
    - **Частота обновления**: {refresh_rate} Hz
    - **Технология**: {tech}
    - **Яркость**: {1200 if screen_type == "Indoor" else 6500} нит
    - **Датчик яркости и температуры**: {sensor}
    """)

with st.expander("Модули", expanded=True):
    st.markdown(f"""
    - **По горизонтали**: {modules_w} шт.
    - **По вертикали**: {modules_h} шт.
    - **Основное количество**: {total_modules} шт.
    - **Резерв**: {reserve_modules} шт.
    - **Итого для заказа**: {total_modules_order} шт.
    """)

if mount_type == "В кабинетах":
    with st.expander("Кабинеты", expanded=True):
        st.markdown(f"""
        - **Модель**: {cabinet_model}
        - **Размер одного**: {cabinet_width} × {cabinet_height} мм
        - **Количество**: {total_cabinets} шт. ({cabinets_w} × {cabinets_h})
        - **Вес одного**: {cabinet_weight_per:.1f} кг
        - **Общий вес**: {total_cabinet_weight:.1f} кг
        """)

with st.expander("Принимающие карты", expanded=True):
    st.markdown(f"""
    - **Модель**: {receiving_card}
    - **Количество**: {num_cards} шт. + 1 резерв = {num_cards_reserve} шт.
    """)

with st.expander("Блоки питания", expanded=True):
    st.markdown(f"""
    - **Мощность**: {psu_power}W
    - **Пиковое потребление**: {peak_power_screen:.1f} кВт
    - **С запасом**: {power_with_reserve:.1f} кВт
    - **Количество**: {num_psu_reserve} шт.
    """)

with st.expander("Процессор/плеер", expanded=True):
    st.markdown(f"""
    - **Модель**: {processor}
    - **Доступно портов**: {PROCESSOR_PORTS.get(processor, 1)}
    - **Необходимое портов**: {math.ceil(total_px / 650000)}
    - **Нагрузка на порт**: {(total_px / (PROCESSOR_PORTS.get(processor, 1) * 650000)) * 100:.1f}%
    """)

with st.expander("Сеть", expanded=True):
    st.markdown(f"""
    - **Тип**: {power_phase}
    - **Ток**: {current:.1f} А (с запасом)
    - **Кабель ВВГ**: {cable_section}
    - **Автомат**: {breaker} А (тип C)
    """)

with st.expander("Каркас и крепёж (монолитный)", expanded=True):
    st.markdown(f"""
    - **Вертикальные профили**: {vert_profiles} шт., длина на отрез {vert_length} мм, общая {vert_profiles * vert_length / 1000:.2f} м
    - **Горизонтальные профили**: {horiz_profiles} шт., длина на отрез {horiz_length} мм, общая {horiz_profiles * horiz_length / 1000:.2f} м
    - **Винты M6 + резьбовые заклёпки M6**: {fasteners_m6} шт. + {reserve_fasteners} шт. (запас 3%)
    - **Магниты {magnet_size}**: {magnets} шт. (округлено до 500 шт.)
    - **Металлические пластины**: {num_plates} шт. (по количеству БП)
    - **Винты 4×16 со сверлом к профилям**: {vinths} шт. + {reserve_vinths} шт. (запас 10%)
    """)

with st.expander("Коммутация", expanded=True):
    st.markdown(f"""
    - **Силовые кабели 220 В**: {num_cables} шт., общая {num_cables * 0.8:.1f} м
    - **Наконечники НВИ**: {nvi} шт. + {reserve_nvi} шт. (запас 10%)
    - **Патч-корды RJ45**: {patch_cords} шт.
    - **Кабель питания приёмной карты от БП**: {num_power_cables} шт., общая {total_power_cable_length:.1f} м + {reserve_power_cables} шт. (запас 10%)
    """)

with st.expander("Вес экрана", expanded=True):
    st.markdown(f"""
    - **Вес модулей**: {weight_modules:.1f} кг
    - **Вес каркаса**: {weight_carcas:.1f} кг
    - **Общий вес**: {total_weight:.1f} кг
    """)

with st.expander("Упаковка и логистика", expanded=True):
    st.markdown(f"""
    - **Количество коробок**: {num_boxes} шт.
    - **Общий вес коробок**: {box_weight} кг
    - **Общий объём коробок**: {box_volume:.2f} м³
    """)

# Схема монтажа (HTML)
if mount_type == "Монолитный":
    st.subheader("Схема монолитного монтажа (вид сверху)")
    html_scheme = """
    <div style="font-family: monospace; background: #1a1a2e; color: #e0e0ff; padding: 20px; border-radius: 12px; border: 1px solid #4a4a8a; overflow-x: auto;">
        <p style="color: #7f5af0; font-weight: bold; text-align: center;">Схема монолитного экрана</p>
        <pre style="margin: 0; white-space: pre;">
┌""" + "─" * (modules_w * 6) + """┐
"""
    for row in range(modules_h):
        line = "│"
        for col in range(modules_w):
            color = "#00ff9d" if (row + col) % 2 == 0 else "#ff6bcb"
            line += f'<span style="color:{color};"> ███ </span>'
        line += "│\n"
        html_scheme += line + "├" + "─" * (modules_w * 6) + "┤\n"

    html_scheme += """└""" + "─" * (modules_w * 6) + """┘
<span style="color:#00ff9d;">███</span> — модуль установлен
        </pre>
    </div>
    """
    st.markdown(html_scheme, unsafe_allow_html=True)
