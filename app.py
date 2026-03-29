import streamlit as st
import math
import json
import datetime
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    pass # Обработка для сред без установленного gspread

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Screen Pro Calculator | MediaLive", layout="wide", page_icon="🖥️")

# --- СОВРЕМЕННЫЙ CSS ДИЗАЙН ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    /* Стили для карточек метрик */
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #151a22 100%);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #2d3748;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #63b3ed;
    }
    .metric-label {
        font-size: 14px;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Стили для кнопок (от GROK, адаптированные) */
    .stButton>button {
        background: linear-gradient(90deg, #3182ce, #2b6cb0); 
        color: white; 
        border: none; 
        border-radius: 8px; 
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02); 
        box-shadow: 0 0 15px rgba(49, 130, 206, 0.5);
    }
    /* Стили для expander */
    div[data-testid="stExpander"] {
        background-color: #1a202c;
        border-radius: 8px;
        border: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# --- СПРАВОЧНИКИ ---
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

# --- ИНИЦИАЛИЗАЦИЯ STATE ---
if "width_mm" not in st.session_state:
    st.session_state.width_mm = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240
if "previous_selected" not in st.session_state:
    st.session_state.previous_selected = "3840 × 2160"

def fit_ratio(ratio):
    ideal = st.session_state.width_mm / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# --- БОКОВАЯ ПАНЕЛЬ: ПРОЕКТ И ФИНАНСЫ ---
st.sidebar.header("📝 Данные проекта")
project_name = st.sidebar.text_input("Имя проекта", value="MediaLive - Новый проект")
client_name = st.sidebar.text_input("Клиент / Заказчик", placeholder="Введите имя клиента")
price_per_m2 = st.sidebar.number_input("Цена за м² (₽)", min_value=0, value=150000, step=5000)

st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Расчёт комплектующих для экранов Qiangli (320×160 мм), Novastar и Mean Well.")

# --- БЛОК 1: РАЗМЕРЫ (С БЕЗОПАСНЫМ ОБНОВЛЕНИЕМ СТЕЙТА) ---
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

col_size1, col_size2 = st.columns(2)

with col_size1:
    selected_label = st.selectbox("Популярные размеры 16:9", list(popular_16_9.keys()), index=2)
    # Перехват изменения селектбокса до рендера width_input
    if selected_label != st.session_state.previous_selected:
        selected_w, selected_h = popular_16_9[selected_label]
        if selected_w is not None:
            st.session_state.width_mm = selected_w
            st.session_state.height_mm = selected_h
        st.session_state.previous_selected = selected_label
        st.rerun()

    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=st.session_state.width_mm, key="width_input")
    st.session_state.width_mm = width_mm

with col_size2:
    st.write("**Подгонка высоты (пропорции):**")
    btn_cols = st.columns(4)
    if btn_cols[0].button("16:9"):
        fit_ratio(1.7777777777777777)
        st.rerun()
    if btn_cols[1].button("4:3"):
        fit_ratio(1.3333333333333333)
        st.rerun()
    if btn_cols[2].button("21:9"):
        fit_ratio(2.3333333333333335)
        st.rerun()
    if btn_cols[3].button("1:1"):
        fit_ratio(1.0)
        st.rerun()

    # Поле высоты БЕЗ key, обновляется через session_state визуально
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=st.session_state.height_mm)
    st.session_state.height_mm = height_mm

st.markdown("---")

# --- БЛОК 2: ОБОРУДОВАНИЕ И ЖЕЛЕЗО ---
col_hw1, col_hw2, col_hw3 = st.columns(3)

with col_hw1:
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)
    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)
    
    if screen_type == "Indoor":
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", INDOOR_PITCHES, index=8) # 2.5
    else:
        pixel_pitch = st.selectbox("Шаг пикселя (мм)", OUTDOOR_PITCHES, index=0) # 2.5

with col_hw2:
    cabinet_model = "Монолит"
    cabinet_width, cabinet_height, cabinet_weight_per = 640, 480, 20.0
    
    if mount_type == "В кабинетах":
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
            cabinet_width = st.number_input("Ширина кабинета (мм)", min_value=320, value=640)
            cabinet_height = st.number_input("Высота кабинета (мм)", min_value=160, value=480)
            cabinet_weight_per = st.number_input("Вес кабинета (кг)", min_value=1.0, value=20.0, step=0.5)
        else:
            cabinet_width, cabinet_height, cabinet_weight_per = selected_data
    else:
        magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

with col_hw3:
    system_type = st.radio("Система управления", ["Синхронный", "Асинхронный"], index=0)
    if system_type == "Синхронный":
        available_processors = ["VC10", "VC2", "VC4", "VC6", "VC16", "VC24", "MCTRL300", "MCTRL600", "MCTRL700", "MCTRL4K", "MCTRL R5", "VX400", "VX600 Pro", "VX1000 Pro", "VX2000 Pro", "VX16S"]
    else:
        available_processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]
    processor = st.selectbox("Процессор/плеер", available_processors, index=0)
    
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680], index=2)
    receiving_card = st.selectbox("Принимающая карта (Novastar)", list(CARD_MAX_PIXELS.keys()), index=5)

# --- ПРОВЕРКА ПОРТОВ (Визуальный блок) ---
real_width = math.ceil(width_mm / 320) * 320
real_height = math.ceil(height_mm / 160) * 160
total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)

required_ports = math.ceil(total_px / 650000)
available_ports = PROCESSOR_PORTS.get(processor, 1)
load_per_port = (total_px / (available_ports * 650000)) * 100 if available_ports > 0 else 100.0

status_text = "✅ Портов хватает" if required_ports <= available_ports else "❌ Недостаточно портов!"
status_color = "#48bb78" if required_ports <= available_ports else "#f56565"

st.markdown(f"""
<div style="padding: 15px; border-radius: 8px; border: 1px solid #2d3748; background: #1a202c; margin-bottom: 20px;">
    <strong style="color: #a0aec0;">Проверка портов процессора {processor}:</strong>&nbsp;&nbsp;
    Доступно: <strong>{available_ports}</strong> &nbsp;|&nbsp;
    Нужно: <strong>{required_ports}</strong> &nbsp;|&nbsp;
    Нагрузка: <strong>{load_per_port:.1f}%</strong> &nbsp;|&nbsp;
    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
</div>
""", unsafe_allow_html=True)
if load_per_port > 90 and required_ports <= available_ports:
    st.warning("⚠️ Нагрузка >90%! Рекомендуем рассмотреть процессор мощнее для запаса.")

# --- БЛОК 3: ПИТАНИЕ И РЕЗЕРВ ---
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    psu_power = st.selectbox("Мощность БП (W)", [200, 300, 400], format_func=lambda x: f"{x}W", index=0)
    power_reserve = st.selectbox("Запас БП по мощности", [0, 10, 20, 30], format_func=lambda x: f"{x}%", index=2)
with col_p2:
    power_phase = st.radio("Подключение к сети", ["Одна фаза (220 В)", "Три фазы (380 В)"], index=0)
    modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)
with col_p3:
    reserve_enabled = st.checkbox("Включить ЗИП (резерв)", value=True)
    reserve_modules_choice = "5%"
    reserve_modules_custom = 0
    reserve_psu_cards = False
    reserve_patch = False
    if reserve_enabled:
        reserve_modules_choice = st.selectbox("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1)
        if reserve_modules_choice == "Свой":
            reserve_modules_custom = st.number_input("Свой резерв (шт.)", min_value=0)
        reserve_psu_cards = st.checkbox("+1 БП и Карта в ЗИП", value=True)
        reserve_patch = st.checkbox("Двойной запас патч-кордов", value=False)

# --- АВТОМАТИЧЕСКИЕ ВЫЧИСЛЕНИЯ ---
modules_w = math.ceil(width_mm / 320)
modules_h = math.ceil(height_mm / 160)
total_modules = modules_w * modules_h

area_m2 = (real_width / 1000) * (real_height / 1000)
total_price_rub = area_m2 * price_per_m2

if reserve_modules_choice != "Свой":
    reserve_percent = int(reserve_modules_choice.replace("%", ""))
    reserve_modules = math.ceil(total_modules * reserve_percent / 100)
else:
    reserve_modules = reserve_modules_custom
total_modules_order = total_modules + reserve_modules

max_power_module = 24.0 if screen_type == "Indoor" else 45.0
peak_power_screen_kw = total_modules * max_power_module / 1000
power_with_reserve_kw = peak_power_screen_kw * (1 + power_reserve / 100)

num_psu = math.ceil(power_with_reserve_kw / (psu_power / 1000))
num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

max_pixels_card = CARD_MAX_PIXELS[receiving_card]
num_cards_by_mod = math.ceil(total_modules / modules_per_card)
num_cards_by_pix = math.ceil(total_px / max_pixels_card)
num_cards = max(num_cards_by_mod, num_cards_by_pix)
num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

# Сеть
voltage = 220 if power_phase == "Одна фаза (220 В)" else 380 * math.sqrt(3)
current = power_with_reserve_kw * 1000 / voltage
cable_section = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм²"
breaker = math.ceil(current * 1.25)

# Каркас и Вес
vert_profiles, horiz_profiles = modules_w + 1, 2 if real_height <= 3000 else 3
total_profile_length = (vert_profiles * (real_height - 40) + horiz_profiles * (real_width - 60)) / 1000

module_weight = 0.37 if screen_type == "Indoor" else 0.5
weight_modules = total_modules_order * module_weight
weight_carcas = total_profile_length * 2 if mount_type == "Монолитный" else 0
total_cabinet_weight = 0
if mount_type == "В кабинетах":
    cabinets_w = math.ceil(real_width / cabinet_width)
    cabinets_h = math.ceil(real_height / cabinet_height)
    total_cabinets = cabinets_w * cabinets_h
    total_cabinet_weight = total_cabinets * cabinet_weight_per
total_weight = weight_modules + weight_carcas + total_cabinet_weight + ((weight_modules + weight_carcas) * 0.05)

# --- ВЫВОД КРАСИВЫХ МЕТРИК ---
st.markdown("---")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Площадь</div><div class="metric-value">{area_m2:.2f} м²</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Разрешение</div><div class="metric-value">{int(real_width/pixel_pitch)} × {int(real_height/pixel_pitch)}</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Пиковая мощность</div><div class="metric-value">{peak_power_screen_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Ориентир. стоимость</div><div class="metric-value">{total_price_rub:,.0f} ₽</div></div>', unsafe_allow_html=True)


# --- ДЕТАЛЬНЫЙ ОТЧЕТ В EXPANDERS ---
st.subheader("📋 Детализация комплектующих")

with st.expander("Модули и ЗИП", expanded=True):
    st.markdown(f"""
    - **Технология:** Qiangli {tech} P{pixel_pitch} {screen_type}
    - **Сетка модулей:** {modules_w} шт (Ш) × {modules_h} шт (В)
    - **В экране:** {total_modules} шт.
    - **ЗИП (Резерв):** {reserve_modules} шт.
    - **Итого к заказу:** **{total_modules_order} шт.**
    """)

if mount_type == "В кабинетах":
    with st.expander("Кабинеты", expanded=True):
        st.markdown(f"""
        - **Модель:** {cabinet_model}
        - **Размер кабинета:** {cabinet_width} × {cabinet_height} мм
        - **Сетка кабинетов:** {cabinets_w} (Ш) × {cabinets_h} (В)
        - **Всего кабинетов:** **{total_cabinets} шт.**
        - **Общий вес кабинетов:** {total_cabinet_weight:.1f} кг
        """)

with st.expander("Управление (Приёмные карты и Процессор)", expanded=True):
    st.markdown(f"""
    - **Процессор:** {processor} ({system_type})
    - **Приёмные карты:** {receiving_card}
    - **Количество карт в экране:** {num_cards} шт.
    - **Карты в ЗИП:** {num_cards_reserve - num_cards} шт.
    - **Итого карт к заказу:** **{num_cards_reserve} шт.**
    """)

with st.expander("Питание и Сеть", expanded=True):
    st.markdown(f"""
    - **Блоки питания:** {psu_power}W
    - **Количество БП в экране:** {num_psu} шт. (с запасом мощности {power_reserve}%)
    - **БП в ЗИП:** {num_psu_reserve - num_psu} шт.
    - **Итого БП к заказу:** **{num_psu_reserve} шт.**
    - **Подключение:** {power_phase}
    - **Вводной автомат:** {breaker} А (тип C)
    - **Рекомендуемый кабель:** {cable_section}
    """)

with st.expander("Каркас, Коммутация и Вес (Монолит)", expanded=False):
    st.markdown(f"""
    - **Магниты {magnet_size if mount_type == "Монолитный" else "N/A"}:** {math.ceil(total_modules * 4 / 500) * 500} шт. (округлено до уп.)
    - **Профили (оценка):** Вертикальных {vert_profiles} шт, Горизонтальных {horiz_profiles} шт.
    - **Сетевые кабели 220В внутри:** ~{num_psu_reserve - 1} шт.
    - **Патч-корды RJ45:** {num_cards_reserve * (2 if reserve_patch else 1)} шт.
    - **Общий расчётный вес экрана:** **~{total_weight:.1f} кг**
    """)


# --- CSS GRID СХЕМА МОНТАЖА (ЗАМЕНА ASCII) ---
if mount_type == "Монолитный":
    st.subheader("📐 Схема монолитного монтажа")
    # Адаптивный CSS Grid
    html_grid = f"""
    <div style="
        display: grid; 
        grid-template-columns: repeat({modules_w}, 1fr); 
        gap: 2px; 
        background-color: #2d3748; 
        padding: 4px;
        width: 100%;
        max-width: 900px;
        border-radius: 4px;
        margin: 0 auto;
    ">
    """
    for row in range(modules_h):
        for col in range(modules_w):
            color = "#48bb78" if (row + col) % 2 == 0 else "#319795"
            html_grid += f'<div style="background-color: {color}; aspect-ratio: 2/1; border-radius: 2px; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold; color: rgba(255,255,255,0.8);">M</div>'
    html_grid += "</div>"
    st.components.v1.html(html_grid, height=int(900 * (modules_h/modules_w)) + 30)

st.markdown("---")

# --- БЛОК 4: ИНТЕГРАЦИИ (FIGMA & GOOGLE SHEETS) ---
st.subheader("🔗 Экспорт и Интеграция")

figma_data = {
    "project_name": project_name,
    "client": client_name,
    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "screen_dimensions_mm": f"{real_width}x{real_height}",
    "resolution_px": f"{int(real_width/pixel_pitch)}x{int(real_height/pixel_pitch)}",
    "area_m2": round(area_m2, 2),
    "pixel_pitch": pixel_pitch,
    "total_modules": total_modules,
    "modules_with_reserve": total_modules_order,
    "cabinet_type": mount_type,
    "receiving_cards": num_cards_reserve,
    "power_supplies": num_psu_reserve,
    "processor": processor,
    "peak_power_kw": round(peak_power_screen_kw, 2),
    "total_weight_kg": round(total_weight, 1),
    "price_per_m2_rub": price_per_m2,
    "total_price_rub": total_price_rub
}

figma_json = json.dumps(figma_data, indent=4, ensure_ascii=False)

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.markdown("**1. Экспорт в Figma (Variables Studio)**")
    st.code(figma_json, language="json")

with col_exp2:
    st.markdown("**2. Сохранение в базу Google Sheets**")
    if st.button("💾 Отправить расчёт в облако"):
        try:
            if "google_sheets" in st.secrets:
                creds_dict = dict(st.secrets["google_sheets"])
                credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                client = gspread.authorize(credentials)
                sheet = client.open("MediaLive_Calculations").sheet1
                
                row_to_insert = [
                    figma_data["date"], project_name, client_name,
                    figma_data["screen_dimensions_mm"], figma_data["area_m2"],
                    figma_data["pixel_pitch"], figma_data["total_price_rub"]
                ]
                sheet.append_row(row_to_insert)
                st.success("✅ Сохранено в Google Sheets!")
            else:
                st.warning("Секреты `st.secrets['google_sheets']` не настроены.")
                st.success("✅ [Mock] Данные сформированы для отправки в базу!")
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")
