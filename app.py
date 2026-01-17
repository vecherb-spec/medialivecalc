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

# Улучшенная таблица потребления (Вт на модуль 320×160)
POWER_CONSUMPTION = {
    "Indoor": {
        range(0, 1.3):   (12, 42),
        range(1.3, 1.8): (9, 32),
        range(1.8, 2.6): (7.5, 26),
        range(2.6, 999): (6.5, 22),
    },
    "Outdoor": {
        range(0, 3.1):   (24, 72),
        range(3.1, 4.1): (20, 60),
        range(4.1, 6.1): (16, 48),
        range(6.1, 999): (13, 40),
    }
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

    cabinet_model = None
    cabinet_w, cabinet_h, cabinet_weight = 640, 480, 20.0

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
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: cabinet_w = st.number_input("Ширина кабинета (мм)", 320, value=640)
            with col_c2: cabinet_h = st.number_input("Высота кабинета (мм)", 160, value=480)
            with col_c3: cabinet_weight = st.number_input("Вес кабинета (кг)", 1.0, value=20.0, step=0.5)
        else:
            sizes = {
                "QM Series (640×480, indoor, ~20 кг)": (640, 480, 20.0),
                "MG Series (960×960, out/in, ~40 кг)": (960, 960, 40.0),
                "QF Series (500×500, rental, ~13.5 кг)": (500, 500, 13.5),
                "QS Series (960×960, outdoor fixed, ~45 кг)": (960, 960, 45.0),
            }
            cabinet_w, cabinet_h, cabinet_weight = sizes[cabinet_model]

with col3:
    st.subheader("Система и частота")
    refresh_rate = st.selectbox("Частота обновления (Hz)", [1920, 2880, 3840, 6000, 7680, 15360], index=2)
    system_type = st.radio("Тип системы", ["Синхронный", "Асинхронный"], index=0)

    if system_type == "Синхронный":
        processors = list(set(list(PROCESSOR_PORTS.keys())[:15]))  # исключаем TB
    else:
        processors = ["TB10 Plus", "TB30", "TB40", "TB50", "TB60"]

    processor = st.selectbox("Процессор / плеер", processors, index=0)

# ─── Дополнительные параметры ────────────────────────────────────────────────
magnet_size = "13 мм"
if mount_type == "Монолитный":
    magnet_size = st.selectbox("Размер магнита", ["10 мм", "13 мм", "17 мм"], index=1)

sensor = "Нет"
if screen_type == "Outdoor":
    sensor = st.radio("Датчик яркости/температуры", ["Нет", "Есть (NSO60 или аналог)"], index=1)

receiving_card = st.selectbox("Принимающая карта", list(CARD_MAX_PIXELS.keys()), index=5)

modules_per_card = st.selectbox("Модулей на карту", [8, 10, 12, 16], index=0)
modules_per_psu = st.selectbox("Модулей на БП", [4, 6, 8, 10], index=2)

power_reserve_pct = st.radio("Запас по питанию", [15, 30, 50], index=1)
psu_power = st.selectbox("Мощность БП (Вт)", [200, 300, 400, 500], index=0)

power_phase = st.radio("Подключение к сети", ["Одна фаза 220 В", "Три фазы 380 В"], index=0)

# Резерв
reserve_enabled = st.checkbox("Включить резервные элементы", value=True)

reserve_modules_pct = 5
reserve_modules_custom = 0
if reserve_enabled:
    res_choice = st.radio("Резерв модулей", ["3%", "5%", "10%", "Свой"], index=1, horizontal=True)
    if res_choice == "3%":   reserve_modules_pct = 3
    elif res_choice == "5%": reserve_modules_pct = 5
    elif res_choice == "10%": reserve_modules_pct = 10
    else:
        reserve_modules_custom = st.number_input("Свой резерв модулей (шт)", 0, value=0)

    reserve_psu_cards = st.checkbox("+1 БП и +1 комплект карт", value=True)
    reserve_patch = st.checkbox("Двойной комплект патч-кордов", value=False)

# ─── Кнопка расчёта ──────────────────────────────────────────────────────────
if st.button("✦ Рассчитать", type="primary", use_container_width=True):

    # ─── Основные размеры ────────────────────────────────────────────────────
    modules_w = math.ceil(width_mm / 320)
    modules_h = math.ceil(height_mm / 160)
    real_w = modules_w * 320
    real_h = modules_h * 160
    total_modules = modules_w * modules_h

    # Резерв модулей
    if reserve_enabled:
        reserve_modules = reserve_modules_custom if res_choice == "Свой" else math.ceil(total_modules * reserve_modules_pct / 100)
    else:
        reserve_modules = 0
    total_modules_order = total_modules + reserve_modules

    # ─── Пиксели и процессор ─────────────────────────────────────────────────
    total_px = (real_w / pixel_pitch) * (real_h / pixel_pitch)
    required_ports = math.ceil(total_px / 650_000)
    avail_ports = PROCESSOR_PORTS.get(processor, 1)
    load_pct = (total_px / (avail_ports * 650_000)) * 100 if avail_ports > 0 else 999

    # ─── Потребление мощности (улучшенная версия) ───────────────────────────
    pitch_int = int(pixel_pitch * 100)
    if screen_type == "Indoor":
        for r, (avg, peak) in POWER_CONSUMPTION["Indoor"].items():
            if pitch_int in r:
                avg_power_mod = avg
                peak_power_mod = peak
                break
        else:
            avg_power_mod, peak_power_mod = 8.0, 24.0
    else:
        for r, (avg, peak) in POWER_CONSUMPTION["Outdoor"].items():
            if pitch_int in r:
                avg_power_mod = avg
                peak_power_mod = peak
                break
        else:
            avg_power_mod, peak_power_mod = 15.0, 45.0

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

    # ─── Сеть ────────────────────────────────────────────────────────────────
    voltage = 220 if power_phase.startswith("Одна") else 380 * math.sqrt(3)
    current = power_with_reserve * 1000 / voltage
    if current < 60:
        cable = "3×16 мм²"
    elif current < 100:
        cable = "3×25 мм²"
    else:
        cable = "3×35 мм² или больше"
    breaker = math.ceil(current * 1.25)

    # ─── Каркас (только монолит) ─────────────────────────────────────────────
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
        total_profile_m = 0
        magnets = 0
        plates = 0
        screws_to_profile = 0
        reserve_screws = 0
        fasteners_m6 = 0
        reserve_fasteners = 0

    # ─── Коммутация ──────────────────────────────────────────────────────────
    power_cables_220 = max(0, num_psu_total - 1)
    nvi_tips = power_cables_220 * 6
    reserve_nvi = math.ceil(nvi_tips * 0.1)

    patch_cords = num_cards_total * (2 if reserve_enabled and reserve_patch else 1)
    power_cables_to_cards = num_cards_total
    reserve_power_cables_to_cards = math.ceil(power_cables_to_cards * 0.1)

    # ─── Вес ─────────────────────────────────────────────────────────────────
    module_weight = 0.37 if screen_type == "Indoor" else 0.50
    modules_weight = total_modules_order * module_weight
    carcas_weight = total_profile_m * 2.2 if mount_type == "Монолитный" else 0
    extra_weight = (modules_weight + carcas_weight) * 0.05
    total_weight = modules_weight + carcas_weight + extra_weight

    if mount_type == "В кабинетах":
        cab_w_count = math.ceil(real_w / cabinet_w)
        cab_h_count = math.ceil(real_h / cabinet_h)
        total_cabinets = cab_w_count * cab_h_count
        cabinets_weight = total_cabinets * cabinet_weight
        total_weight += cabinets_weight
    else:
        total_cabinets = 0
        cabinets_weight = 0

    # ─── Упаковка ────────────────────────────────────────────────────────────
    boxes = math.ceil(total_modules_order / 40)
    box_weight_total = boxes * 22
    box_volume_total = boxes * 0.06

    # ─── Вывод результатов ───────────────────────────────────────────────────
    st.success("Расчёт завершён ✓")

    with st.expander("Основные характеристики", expanded=True):
        cols = st.columns([2, 3])
        with cols[0]:
            st.markdown(f"""
            **Размер реальный**  
            {real_w} × {real_h} мм  
            **Площадь**  
            {real_w * real_h / 1_000_000:.2f} м²  
            **Разрешение**  
            {int(real_w / pixel_pitch)} × {int(real_h / pixel_pitch)} px
            """)
        with cols[1]:
            st.markdown(f"""
            **Модулей** {total_modules} + резерв {reserve_modules} = **{total_modules_order}** шт.  
            **Процессор** {processor} — {avail_ports} портов  
            **Нагрузка** {load_pct:.1f}%  {'✅' if load_pct <= 85 else '⚠️' if load_pct <= 95 else '❌'}
            """)

    tab1, tab2, tab3, tab4 = st.tabs(["Модули & Питание", "Коммутация", "Каркас/Вес", "Схема"])

    with tab1:
        st.markdown(f"""
        **Модули** — {total_modules_order} шт. (резерв {reserve_modules})

        **Потребление** (примерно):  
        • Среднее: {avg_power_screen:.1f} кВт  
        • Пиковое: {peak_power_screen:.1f} кВт  
        • С запасом {power_reserve_pct}%: **{power_with_reserve:.1f} кВт**

        **Блоки питания** {psu_power} Вт — **{num_psu_total}** шт.
        """)

        st.markdown(f"""
        **Принимающие карты** {receiving_card}  
        • По модулям: {cards_by_modules}  
        • По пикселям: {cards_by_pixels}  
        → **Итого: {num_cards} + резерв = {num_cards_total}** шт.
        """)

    with tab2:
        st.markdown(f"""
        **Сеть** — {power_phase}  
        • Ток: {current:.1f} А  
        • Рекомендуемый кабель: **{cable}**  
        • Автомат: **{breaker}** А (тип C)

        **Коммутация**  
        • Силовые кабели 220 В: {power_cables_220} шт.  
        • Наконечники НВИ: {nvi_tips} + запас {reserve_nvi}  
        • Патч-корды RJ45: **{patch_cords}** шт.  
        • Кабели питания карт: {power_cables_to_cards} + запас {reserve_power_cables_to_cards}
        """)

    with tab3:
        if mount_type == "Монолитный":
            st.markdown(f"""
            **Каркас**  
            • Вертикальные профили: {vert_profiles} × {vert_len} мм  
            • Горизонтальные: {horiz_profiles} × {horiz_len} мм  
            • Общая длина профиля: {total_profile_m:.1f} м

            **Крепёж**  
            • Магниты {magnet_size}: ~{magnets} шт.  
            • Пластины: {plates}  
            • Винты к профилям: {screws_to_profile} + запас {reserve_screws}  
            • Винты/заклёпки M6: {fasteners_m6} + запас {reserve_fasteners}
            """)

        st.markdown(f"""
        **Общий вес экрана** ≈ **{total_weight:.0f} кг**  
        • Модули: {modules_weight:.0f} кг  
        • Каркас/кабинеты: {(carcas_weight + cabinets_weight):.0f} кг  
        • Доп. элементы: {extra_weight:.0f} кг
        """)

        st.markdown(f"""
        **Упаковка**  
        • Коробок: **{boxes}** шт.  
        • Вес: ≈ {box_weight_total} кг  
        • Объём: ≈ {box_volume_total:.2f} м³
        """)

    with tab4:
        if mount_type == "Монолитный":
            st.subheader("Схема монтажа (вид сверху)")
            
            cell_width = 5
            total_width = modules_w * cell_width
            
            html_scheme = f"""
            <div style="font-family:monospace; background:#1a1a2e; color:#e0e0ff; padding:20px; border-radius:12px; border:1px solid #4a4a8a; overflow-x:auto;">
            <p style="color:#7f5af0; font-weight:bold; text-align:center;">Схема монолитного экрана</p>
            <pre style="margin:0; white-space:pre;">
┌{'─' * total_width}┐
"""
            for row in range(modules_h):
                line = "│"
                for col in range(modules_w):
                    color = "#00ff9d" if (row + col) % 2 == 0 else "#ff6bcb"
                    line += f'<span style="color:{color};"> ███ </span>'
                line += "│"
                html_scheme += line + "\n"
                if row < modules_h - 1:
                    html_scheme += f"├{'─' * total_width}┤\n"
            
            html_scheme += f"""└{'─' * total_width}┘
            </pre>
            <div style="margin-top:12px; font-size:0.95em;">
                <span style="color:#00ff9d;">███</span> — модуль установлен (шахматный порядок)
            </div>
            </div>
            """
            st.markdown(html_scheme, unsafe_allow_html=True)
        else:
            st.info("Схема доступна только для монолитного монтажа")

    # PDF ────────────────────────────────────────────────────────────────
    def generate_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        y = h - 60

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Расчёт LED-экрана MediaLive")
        y -= 30
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y -= 40

        def section(title, items):
            nonlocal y
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, title)
            y -= 20
            c.setFont("Helvetica", 10)
            for line in items:
                c.drawString(70, y, line)
                y -= 14
            y -= 10

        section("Экран", [
            f"Реальный размер: {real_w} × {real_h} мм",
            f"Площадь: {real_w*real_h/1_000_000:.2f} м²",
            f"Разрешение: {int(real_w/pixel_pitch)} × {int(real_h/pixel_pitch)} px",
            f"Шаг пикселя: {pixel_pitch} мм, {tech}",
            f"Частота: {refresh_rate} Hz"
        ])

        section("Модули и резерв", [
            f"Всего модулей: {total_modules}",
            f"Резерв: {reserve_modules}",
            f"Заказ: {total_modules_order} шт."
        ])

        section("Питание", [
            f"Пиковое: {peak_power_screen:.1f} кВт",
            f"С запасом: {power_with_reserve:.1f} кВт",
            f"БП {psu_power} Вт × {num_psu_total} шт.",
            f"Карты {receiving_card} × {num_cards_total} шт."
        ])

        section("Вес", [f"Примерный общий вес: {total_weight:.0f} кг"])

        c.save()
        buffer.seek(0)
        return buffer

    pdf_data = generate_pdf()
    st.download_button(
        "📄 Скачать PDF-отчёт",
        pdf_data,
        file_name=f"LED_calc_{datetime.now():%Y%m%d_%H%M}.pdf",
        mime="application/pdf"
    )
