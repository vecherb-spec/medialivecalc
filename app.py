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
st.markdown("Профессиональный расчёт экранов Qiangli 320×160 мм — быстро и точно")

# Данные процессоров и портов (исправлено)
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
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", [0.8, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0, 5.0, 6.67, 8.0, 10.0], index=8)
    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

with col3:
    st.subheader("Частота и система")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    # Фильтрация процессоров
    if system_type == "Синхронный":
        vc_processors = ["VC2", "VC4", "VC6", "VC10", "VC16", "VC24"]
        mctrl_processors = ["MCTRL300", "MCTRL600", "MCTRL700", "MCTRL4K", "MCTRL R5"]
        vx_processors = ["VX400", "VX600 Pro", "VX1000 Pro", "VX2000 Pro", "VX16S"]
        available_processors = vc_processors + mctrl_processors + vx_processors
    else:
        available_processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]
    processor = st.selectbox("Процессор/плеер", available_processors, index=0)

# Магнит для монолитного
magnet_size = "13 мм"
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

# Датчик для outdoor
sensor = "Нет"
if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости и температуры", ["Нет", "Есть (NSO60 или аналог)"], index=1)

# Карта
receiving_card = st.selectbox("Принимающая карта (Novastar)", list(CARD_MAX_PIXELS.keys()), index=5)

# Ориентиры
modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)  # дефолт 8
modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10], index=2)  # дефолт 8

# Запас по питанию (15% или 30%)
power_reserve = st.radio("Запас по питанию", [15, 30], index=1)

# Мощность БП
psu_power = st.selectbox("Мощность БП (Вт)", [200, 300, 400], index=2)

# Сеть
power_phase = st.radio("Подключение к сети", ["Одна фаза (220 В)", "Три фазы (380 В)"], index=0)

# Резерв
reserve_enabled = st.checkbox("Включить резервные элементы?", value=True)
reserve_modules_percent = 5
reserve_modules_custom = 0
reserve_psu_cards = False
reserve_patch = False
if reserve_enabled:
    reserve_modules_choice = st.radio("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1)
    if reserve_modules_choice == "Свой":
        reserve_modules_custom = st.number_input("Свой резерв модулей (шт.)", value=0)
    reserve_psu_cards = st.checkbox("+1 к БП и картам", value=True)
    reserve_patch = st.checkbox("Резервные патч-корды (×2)", value=False)

# Кнопка расчёта
if st.button("Рассчитать", type="primary", use_container_width=True):
    # Основные расчёты
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    # Резерв модулей
    reserve_modules = math.ceil(total_modules * reserve_modules_percent / 100) if reserve_modules_choice != "Свой" else reserve_modules_custom
    total_modules_order = total_modules + reserve_modules

    # Потребление
    avg_power_module = 8.0 if screen_type == "Indoor" else 15.0
    max_power_module = 24.0 if screen_type == "Indoor" else 45.0
    avg_power_screen = total_modules * avg_power_module / 1000
    peak_power_screen = total_modules * max_power_module / 1000
    power_with_reserve = peak_power_screen * (1 + power_reserve / 100)

    # БП
    psu_power_kw = psu_power / 1000
    num_psu = math.ceil(power_with_reserve / psu_power_kw)
    num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

    # Карты
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

    # Схема монтажа (HTML, вариант 2)
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

    with st.expander("Принимающие карты", expanded=True):
        st.markdown(f"""
        - **Модель**: {receiving_card}
        - **Количество**: {num_cards} шт. + 1 резерв = {num_cards_reserve} шт.
        """)

    with st.expander("Блоки питания", expanded=True):
        st.markdown(f"""
        - **Мощность**: {psu_power} Вт
        - **Пиковое потребление**: {peak_power_screen:.1f} кВт
        - **С запасом**: {power_with_reserve:.1f} кВт
        - **Количество**: {num_psu} шт. + 1 резерв = {num_psu_reserve} шт.
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
