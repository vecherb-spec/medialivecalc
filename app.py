import streamlit as st
import math

# ===============================
# Конфигурация страницы
# ===============================
st.set_page_config(page_title="MediaLive LED Calculator", layout="wide", page_icon="🖥️")

st.markdown("""
<style>
.main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
.stButton>button {background: linear-gradient(90deg, #667eea, #764ba2); color: white; border-radius: 12px; padding: 12px 24px; font-weight: bold;}
.card {background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px;}
h1, h2, h3 {color: #a78bfa !important;}
</style>
""", unsafe_allow_html=True)

st.title("🖥️ MediaLive LED Engineering Calculator")

# ===============================
# Процессоры
# ===============================
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

PORT_MAX_PIXELS = 650000

# ===============================
# Приёмные карты
# ===============================
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

# ===============================
# Ввод параметров
# ===============================
col1, col2, col3 = st.columns(3)

with col1:
    width_mm = st.number_input("Ширина экрана (мм)", 320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", 160, step=160, value=2880)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"])

with col2:
    mount_type = st.radio("Тип монтажа", ["Монолитный", "В кабинетах"])
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", [1.25,1.56,1.86,2.5,3.07,4,5,6.67])

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

# ===============================
# Расчёт
# ===============================
if st.button("Рассчитать", use_container_width=True):

    # Геометрия
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_width = modules_w * 320
    real_height = modules_h * 160
    total_modules = modules_w * modules_h

    # Резерв
    reserve_map = {"3%":3,"5%":5,"10%":10}
    reserve_modules_percent = reserve_map.get(reserve_modules_choice, 0)
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
    max_power_module = 24 if screen_type == "Indoor" else 45
    peak_power_screen = total_modules * max_power_module / 1000
    power_with_reserve = peak_power_screen * (1 + power_reserve/100)
    num_psu = math.ceil(power_with_reserve / (psu_power/1000))

    # Электрика
    if power_phase == "Одна фаза (220 В)":
        current = power_with_reserve * 1000 / 220
        cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
    else:
        current = power_with_reserve * 1000 / (math.sqrt(3) * 380)
        cable_section = "5×10 мм²" if current < 40 else "5×16 мм²" if current < 63 else "5×25 мм²"

    breaker = math.ceil(current * 1.25)

    # Процессор
    available_ports = PROCESSOR_PORTS[processor]
    required_ports = math.ceil(total_px / PORT_MAX_PIXELS)
    load_per_port = (total_px / (available_ports * PORT_MAX_PIXELS)) * 100

    # Каркас
    vert_profiles = modules_w + 1
    vert_length = real_height - 40
    horiz_profiles = 2 if real_height <= 3000 else 3
    horiz_length = real_width - 60
    total_profile_length = (vert_profiles * vert_length + horiz_profiles * horiz_length) / 1000

    # Крепёж
    plates = num_psu
    screws = plates * 4
    reserve_screws = math.ceil(screws * 0.1)

    # Коммутация
    power_cables = num_psu
    patch_cords = num_cards
    nvi = power_cables * 6

    # Вес
    module_weight = 0.37 if screen_type == "Indoor" else 0.5
    weight_modules = total_modules_order * module_weight
    weight_frame = total_profile_length * 2
    total_weight = weight_modules + weight_frame

    # Упаковка
    num_boxes = math.ceil(total_modules_order / 40)
    box_weight = num_boxes * 22
    box_volume = num_boxes * 0.06

    # ===============================
    # Отчёт
    # ===============================
    st.success("Расчёт выполнен")

    with st.expander("Экран", expanded=True):
        st.markdown(f"""
- Размер: {real_width} × {real_height} мм  
- Разрешение: {int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)} px  
- Площадь: {real_width*real_height/1_000_000:.2f} м²  
- Частота: {refresh_rate} Гц
""")

    with st.expander("Модули", expanded=True):
        st.markdown(f"""
- По горизонтали: {modules_w}
- По вертикали: {modules_h}
- Основные: {total_modules}
- Резерв: {reserve_modules}
- Итого: {total_modules_order}
""")

    with st.expander("Приёмные карты", expanded=True):
        st.markdown(f"""
- Модель: {receiving_card}
- Количество: {num_cards} шт
""")

    with st.expander("Питание и сеть", expanded=True):
        st.markdown(f"""
- Пиковая мощность: {peak_power_screen:.1f} кВт
- С запасом: {power_with_reserve:.1f} кВт
- Блоки питания: {num_psu} шт
- Ток: {current:.1f} А
- Кабель: {cable_section}
- Автомат: {breaker} А
""")

    with st.expander("Процессор", expanded=True):
        st.markdown(f"""
- Модель: {processor}
- Портов: {available_ports}
- Требуется портов: {required_ports}
- Нагрузка на порт: {load_per_port:.1f} %
""")

    with st.expander("Каркас", expanded=True):
        st.markdown(f"""
- Вертикальные профили: {vert_profiles} шт × {vert_length} мм  
- Горизонтальные профили: {horiz_profiles} шт × {horiz_length} мм  
- Общая длина профиля: {total_profile_length:.1f} м
""")

    with st.expander("Крепёж и коммутация", expanded=True):
        st.markdown(f"""
- Металлические пластины: {plates} шт
- Винты: {screws} шт + {reserve_screws} шт запас
- Силовые кабели: {power_cables} шт
- Патч-корды: {patch_cords} шт
- Наконечники НВИ: {nvi} шт
""")

    with st.expander("Вес и логистика", expanded=True):
        st.markdown(f"""
- Вес модулей: {weight_modules:.1f} кг
- Вес каркаса: {weight_frame:.1f} кг
- Общий вес: {total_weight:.1f} кг

- Коробки: {num_boxes} шт
- Вес коробок: {box_weight} кг
- Объём: {box_volume:.2f} м³
""")

    if required_ports > available_ports:
        st.error("❌ Процессор не справляется с данным разрешением!")

    if load_per_port > 80:
        st.warning("⚠ Нагрузка на порт превышает 80% — рекомендуется процессор классом выше.")
