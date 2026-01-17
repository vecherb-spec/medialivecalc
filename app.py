import streamlit as st
import math
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

# ─── Конфигурация страницы ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Калькулятор LED-экранов MediaLive",
    layout="wide",
    page_icon="🖥️"
)

# ─── Стили ───────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .main {background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);}
    .stButton>button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white; border: none; border-radius: 12px;
        padding: 12px 24px; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
    }
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 15px 0;
    }
    h1, h2, h3 {color: #a78bfa !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ Калькулятор LED-экранов MediaLive")
st.markdown("Расчёт комплектующих для модульных экранов Qiangli 320×160 мм")

# ─── Справочники ─────────────────────────────────────────────────────────────
PROCESSOR_PORTS = {
    "VX400": 4, "VX600 Pro": 6, "VX1000 Pro": 10, "VX2000 Pro": 20, "VX16S": 16,
    "VC2": 2, "VC4": 4, "VC6": 6, "VC10": 10, "VC16": 16, "VC24": 24,
    "MCTRL300": 2, "MCTRL600": 4, "MCTRL700": 6, "MCTRL4K": 16, "MCTRL R5": 8,
    "TB10 Plus": 1, "TB30": 1, "TB40": 2, "TB50": 2, "TB60": 4
}

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

INDOOR_PITCHES = [0.8, 0.9, 1.0, 1.25, 1.37, 1.53, 1.66, 1.86, 2.0, 2.5, 3.07, 4.0]
OUTDOOR_PITCHES = [2.5, 3.07, 4.0, 5.0, 6.0, 6.66, 8.0, 10.0]

# Улучшенная таблица потребления (Вт на модуль 320×160) — ИСПРАВЛЕНО
POWER_CONSUMPTION = {
    "Indoor": [
        (0.0,  1.299,  12.0,  42.0),  # до P1.25
        (1.3,  1.799,   9.0,  32.0),
        (1.8,  2.599,   7.5,  26.0),
        (2.6,  999.0,   6.5,  22.0),
    ],
    "Outdoor": [
        (0.0,  3.099,  24.0,  72.0),
        (3.1,  4.099,  20.0,  60.0),
        (4.1,  6.099,  16.0,  48.0),
        (6.1, 999.0,   13.0,  40.0),
    ]
}

# ─── Ввод данных ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Размер и тип")
    width_mm = st.number_input("Ширина экрана (мм)", min_value=320, step=320, value=3840)
    height_mm = st.number_input("Высота экрана (мм)", min_value=160, step=160, value=2880)
    screen_type = st.radio("Тип экрана", ["Indoor", "Outdoor"], index=0)

with col2:
    st.subheader("Монтаж и шаг")
    mount_type = st.radio("Тип монтажа", ["В кабинетах", "Монолитный"], index=1)

    pitches = INDOOR_PITCHES if screen_type == "Indoor" else OUTDOOR_PITCHES
    pixel_pitch = st.selectbox("Шаг пикселя (мм)", pitches, index=2 if screen_type == "Indoor" else 0)

    tech = st.selectbox("Технология модуля", ["SMD", "COB", "GOB"], index=0)

    cabinet_w, cabinet_h, cabinet_weight = 640, 480, 20.0
    cabinet_model = None

    if mount_type == "В кабинетах":
        cabinet_options = [
            "QM Series (640×480, indoor, ~20 кг)",
            "MG Series (960×960, out/in, ~40 кг)",
            "QF Series (500×500, rental, ~13.5 кг)",
            "QS Series (960×960, outdoor fixed, ~45 кг)",
            "Custom"
        ]
        cabinet_model = st.selectbox("Модель кабинета", cabinet_options, index=0)

        if cabinet_model == "Custom":
            c1, c2, c3 = st.columns(3)
            with c1: cabinet_w = st.number_input("Ширина кабинета (мм)", min_value=320, value=640)
            with c2: cabinet_h = st.number_input("Высота кабинета (мм)", min_value=160, value=480)
            with c3: cabinet_weight = st.number_input("Вес кабинета (кг)", min_value=1.0, value=20.0, step=0.5)
        else:
            sizes = {
                "QM Series (640×480, indoor, ~20 кг)": (640, 480, 20.0),
                "MG Series (960×960, out/in, ~40 кг)": (960, 960, 40.0),
                "QF Series (500×500, rental, ~13.5 кг)": (500, 500, 13.5),
                "QS Series (960×960, outdoor fixed, ~45 кг)": (960, 960, 45.0),
            }
            cabinet_w, cabinet_h, cabinet_weight = sizes.get(cabinet_model, (640, 480, 20.0))

with col3:
    st.subheader("Система и частота")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680, 15360], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    if system_type == "Синхронный":
        processors = [p for p in PROCESSOR_PORTS.keys() if p not in ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]]
    else:
        processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]

    processor = st.selectbox("Процессор / плеер", processors, index=0)

# ─── Дополнительные параметры ────────────────────────────────────────────────
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)
else:
    magnet_size = "—"

if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости/температуры", ["Нет", "Есть (NSO60 или аналог)"], index=1)
else:
    sensor = "Нет"

receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()), index=5)
modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)
modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10], index=2)

power_reserve_pct = st.radio("Запас по питанию (%)", [15, 30, 50], index=1)
psu_power = st.selectbox("Мощность БП (Вт)", [200, 300, 400, 500], index=1)

power_phase = st.radio("Подключение к сети", ["Одна фаза 220 В", "Три фазы 380 В"], index=0)

reserve_enabled = st.checkbox("Включить резервные элементы", value=True)

reserve_modules_pct = 5
reserve_modules_custom = 0
res_choice = "5%"

if reserve_enabled:
    res_choice = st.radio("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1, horizontal=True)
    if res_choice == "3%": reserve_modules_pct = 3
    elif res_choice == "5%": reserve_modules_pct = 5
    elif res_choice == "10%": reserve_modules_pct = 10
    else:
        reserve_modules_custom = st.number_input("Свой резерв модулей (шт)", min_value=0, value=0)

    reserve_psu_cards = st.checkbox("+1 БП и +1 комплект карт", value=True)
    reserve_patch = st.checkbox("Двойной комплект патч-кордов", value=False)

# ─── Кнопка расчёта ──────────────────────────────────────────────────────────
if st.button("✦ Рассчитать", type="primary", use_container_width=True):

    # Основные размеры
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_w = modules_w * 320
    real_h = modules_h * 160
    total_modules = modules_w * modules_h

    # Резерв модулей
    reserve_modules = reserve_modules_custom if res_choice == "Свой" else math.ceil(total_modules * reserve_modules_pct / 100)
    if not reserve_enabled:
        reserve_modules = 0
    total_modules_order = total_modules + reserve_modules

    # Пиксели и проверка процессора
    total_px = (real_w / pixel_pitch) * (real_h / pixel_pitch)
    required_ports = math.ceil(total_px / 650_000)
    avail_ports = PROCESSOR_PORTS.get(processor, 1)
    load_pct = (total_px / (avail_ports * 650_000)) * 100 if avail_ports > 0 else 999

    # Потребление мощности — ИСПРАВЛЕННАЯ ЛОГИКА
    avg_power_mod = 8.0
    peak_power_mod = 24.0
    found = False
    for min_p, max_p, avg, peak in POWER_CONSUMPTION.get(screen_type, []):
        if min_p <= pixel_pitch < max_p:
            avg_power_mod = avg
            peak_power_mod = peak
            found = True
            break
    if not found:
        avg_power_mod = 15.0 if screen_type == "Outdoor" else 8.0
        peak_power_mod = 45.0 if screen_type == "Outdoor" else 24.0

    avg_power_screen = total_modules * avg_power_mod / 1000
    peak_power_screen = total_modules * peak_power_mod / 1000
    power_with_reserve = peak_power_screen * (1 + power_reserve_pct / 100)

    # Блоки питания
    psu_kw = psu_power / 1000
    num_psu = math.ceil(power_with_reserve / psu_kw)
    num_psu_total = num_psu + 1 if reserve_enabled and reserve_psu_cards else num_psu

    # Принимающие карты
    max_px_card = CARD_MAX_PIXELS[receiving_card]
    cards_by_modules = math.ceil(total_modules / modules_per_card)
    cards_by_pixels = math.ceil(total_px / max_px_card)
    num_cards = max(cards_by_modules, cards_by_pixels)
    num_cards_total = num_cards + 1 if reserve_enabled and reserve_psu_cards else num_cards

    # Сеть
    voltage = 220 if power_phase == "Одна фаза 220 В" else 380 * math.sqrt(3)
    current = power_with_reserve * 1000 / voltage
    cable = "3×16 мм²" if current < 60 else "3×25 мм²" if current < 100 else "3×35 мм² или больше"
    breaker = math.ceil(current * 1.25)

    # Каркас (монолитный)
    if mount_type == "Монолитный":
        vert_profiles = modules_w + 1
        vert_len = real_h - 40
        horiz_profiles = 2 if real_h <= 3000 else 3
        horiz_len = real_w - 60
        total_profile_m = (vert_profiles * vert_len + horiz_profiles * horiz_len) / 1000

        fasteners_m6 = int(horiz_profiles * vert_profiles * (2/3))
        reserve_fasteners = math.ceil(fasteners_m6 * 0.03)

        magnets = math.ceil(total_modules * 4 / 500) * 500
        plates = num_psu_total
        screws_to_profile = plates * 4
        reserve_screws = math.ceil(screws_to_profile * 0.1)
    else:
        total_profile_m = fasteners_m6 = reserve_fasteners = magnets = plates = screws_to_profile = reserve_screws = 0

    # Коммутация
    power_cables_220 = max(0, num_psu_total - 1)
    nvi_tips = power_cables_220 * 6
    reserve_nvi = math.ceil(nvi_tips * 0.1)
    patch_cords = num_cards_total * (2 if reserve_enabled and reserve_patch else 1)
    power_cables_to_cards = num_cards_total
    reserve_power_cables = math.ceil(power_cables_to_cards * 0.1)

    # Вес
    module_weight = 0.37 if screen_type == "Indoor" else 0.50
    modules_weight = total_modules_order * module_weight
    carcas_weight = total_profile_m * 2.2 if mount_type == "Монолитный" else 0
    cabinets_weight = 0
    if mount_type == "В кабинетах":
        cab_w_count = math.ceil(real_w / cabinet_w)
        cab_h_count = math.ceil(real_h / cabinet_h)
        total_cabinets = cab_w_count * cab_h_count
        cabinets_weight = total_cabinets * cabinet_weight
    else:
        total_cabinets = 0
    extra_weight = (modules_weight + carcas_weight + cabinets_weight) * 0.05
    total_weight = modules_weight + carcas_weight + cabinets_weight + extra_weight

    # Упаковка
    boxes = math.ceil(total_modules_order / 40)
    box_weight_total = boxes * 22
    box_volume_total = boxes * 0.06

    # ─── Вывод результатов ───────────────────────────────────────────────────
    st.success("Расчёт завершён успешно ✓")

    with st.expander("Основные характеристики экрана", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            **Реальный размер:** {real_w} × {real_h} мм  
            **Площадь:** {real_w * real_h / 1_000_000:.2f} м²  
            **Разрешение:** {int(real_w / pixel_pitch)} × {int(real_h / pixel_pitch)} px  
            **Шаг пикселя:** {pixel_pitch} мм ({tech})
            """)
        with c2:
            st.markdown(f"""
            **Модулей:** {total_modules} + {reserve_modules} резерв = **{total_modules_order}** шт.  
            **Процессор:** {processor} ({avail_ports} портов)  
            **Нагрузка на порт:** {load_pct:.1f}% {'✅' if load_pct <= 90 else '⚠️' if load_pct <= 100 else '❌'}
            """)

    tab1, tab2, tab3, tab4 = st.tabs(["Питание и карты", "Коммутация и сеть", "Каркас и вес", "Схема монтажа"])

    with tab1:
        st.markdown(f"""
        **Потребление:**  
        • Среднее: {avg_power_screen:.1f} кВт  
        • Пиковое: {peak_power_screen:.1f} кВт  
        • С запасом {power_reserve_pct}%: **{power_with_reserve:.1f} кВт**

        **Блоки питания** {psu_power} Вт — **{num_psu_total}** шт.

        **Принимающие карты** {receiving_card}:  
        • По модулям: {cards_by_modules} шт.  
        • По пикселям: {cards_by_pixels} шт.  
        → **Итого: {num_cards_total}** шт.
        """)

    with tab2:
        st.markdown(f"""
        **Электросеть:** {power_phase}  
        • Ток: {current:.1f} А  
        • Кабель: **{cable}**  
        • Автомат: **{breaker}** А (C)

        **Коммутация:**  
        • Силовые кабели 220В: {power_cables_220} шт.  
        • НВИ наконечники: {nvi_tips} + {reserve_nvi} запас  
        • Патч-корды RJ45: **{patch_cords}** шт.  
        • Кабели питания карт: {power_cables_to_cards} + {reserve_power_cables} запас
        """)

    with tab3:
        if mount_type == "Монолитный":
            st.markdown(f"""
            **Каркас:**  
            • Профиль общий: {total_profile_m:.1f} м  
            • Магниты {magnet_size}: {magnets} шт.  
            • Пластины: {plates} шт.  
            • Винты к профилям: {screws_to_profile} + {reserve_screws} запас  
            • Крепёж M6: {fasteners_m6} + {reserve_fasteners} запас
            """)

        if mount_type == "В кабинетах":
            st.markdown(f"**Кабинеты:** {total_cabinets} шт. ({cabinet_model or 'Custom'}), вес {cabinets_weight:.1f} кг")

        st.markdown(f"""
        **Общий вес экрана:** ≈ **{total_weight:.0f} кг**  
        **Упаковка:** {boxes} коробок, ≈ {box_weight_total} кг, {box_volume_total:.2f} м³
        """)

    with tab4:
        if mount_type == "Монолитный":
            st.subheader("Схема монолитного монтажа (вид сверху)")

            cell_width = 5
            total_width = modules_w * cell_width

            html_scheme = f"""
            <div style="font-family:monospace; background:#1a1a2e; color:#e0e0ff; padding:20px; border-radius:12px; border:1px solid #4a4a8a; overflow-x:auto;">
                <p style="color:#7f5af0; font-weight:bold; text-align:center;">Схема монолитного экрана {modules_w} × {modules_h} модулей</p>
                <pre style="margin:0; white-space:pre;">
┌{'─' * total_width}┐
"""
            for row in range(modules_h):
                line = "│"
                for col in range(modules_w):
                    color = "#00ff9d" if (row + col) % 2 == 0 else "#ff6bcb"
                    line += f'<span style="color:{color};"> ███ </span>'
                line += "│\n"
                html_scheme += line
                if row < modules_h - 1:
                    html_scheme += f"├{'─' * total_width}┤\n"

            html_scheme += f"""└{'─' * total_width}┘
                </pre>
                <div style="margin-top:12px; font-size:0.95em;">
                    <span style="color:#00ff9d;">███</span> — модуль (шахматный порядок для наглядности)
                </div>
            </div>
            """
            st.markdown(html_scheme, unsafe_allow_html=True)
        else:
            st.info("Схема доступна только для монолитного монтажа")

    # ─── PDF отчёт ───────────────────────────────────────────────────────────
    def generate_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 70

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, y, "Расчёт LED-экрана MediaLive")
        y -= 40
        c.setFont("Helvetica", 11)
        c.drawCentredString(width/2, y, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        y -= 50

        def add_line(text):
            nonlocal y
            c.drawString(60, y, text)
            y -= 18

        add_line(f"Размер: {real_w} × {real_h} мм ({real_w*real_h/1_000_000:.2f} м²)")
        add_line(f"Разрешение: {int(real_w/pixel_pitch)} × {int(real_h/pixel_pitch)} px")
        add_line(f"Шаг: {pixel_pitch} мм, {tech}, {refresh_rate} Hz")
        y -= 20
        add_line(f"Модулей: {total_modules_order} шт. (в т.ч. резерв {reserve_modules})")
        add_line(f"БП {psu_power} Вт: {num_psu_total} шт.")
        add_line(f"Карты {receiving_card}: {num_cards_total} шт.")
        add_line(f"Общий вес ≈ {total_weight:.0f} кг")
        add_line(f"Пиковое потребление с запасом: {power_with_reserve:.1f} кВт")

        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf()
    st.download_button(
        label="📄 Скачать PDF-отчёт",
        data=pdf_buffer,
        file_name=f"MediaLive_LED_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )
