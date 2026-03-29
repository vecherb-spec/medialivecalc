import streamlit as st
import math
import json
import datetime
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    pass # Обработка для сред без установленного gspread

# --- Настройка страницы ---
st.set_page_config(page_title="LED Screen Pro Calculator", layout="wide", page_icon="🖥️")

# --- CSS стили (Современный UI/UX) ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
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
    div[data-testid="stExpander"] {
        background-color: #1a202c;
        border-radius: 8px;
        border: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# --- Инициализация Session State ---
if 'height_mm' not in st.session_state:
    st.session_state.height_mm = 1920
if 'prev_popular' not in st.session_state:
    st.session_state.prev_popular = "Не выбрано"

# Константы модулей Qiangli
MOD_W = 320
MOD_H = 160

# --- Функции помощники ---
def round_to_mod(value, step):
    """Округление до ближайшего кратного размера модуля"""
    return max(step, int(round(value / step)) * step)

# --- Боковая панель: Данные проекта и цены ---
st.sidebar.header("📝 Данные проекта")
project_name = st.sidebar.text_input("Имя проекта", value="MediaLive - Новый проект")
client_name = st.sidebar.text_input("Клиент / Заказчик", placeholder="Введите имя клиента")
price_per_m2 = st.sidebar.number_input("Цена за м² (₽)", min_value=0, value=150000, step=5000)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Оборудование")
env_type = st.sidebar.selectbox("Тип экрана", ["Indoor (Интерьерный)", "Outdoor (Уличный)"])
pixel_pitch = st.sidebar.selectbox("Шаг пикселя (P)", [1.53, 1.86, 2.0, 2.5, 3.0, 4.0, 5.0])
tech_type = st.sidebar.selectbox("Технология", ["SMD", "DIP", "COB"])
processor = st.sidebar.selectbox("Процессор (Novastar)", ["VC10", "VX4S", "VX6S", "VX1000", "H-Series"])
cabinet_type = st.sidebar.selectbox("Тип монтажа", ["Монолитный (магниты/профиль)", "Кабинеты (Железные)", "Кабинеты (Die-cast алюминий)"])

# --- Основной экран: Размеры ---
st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Расчёт комплектующих на базе модулей Qiangli (320×160 мм), Novastar и Mean Well.")

col_w, col_h = st.columns(2)
with col_w:
    width_input = st.number_input("Ширина (мм)", min_value=MOD_W, step=MOD_W, value=3200, key="width_key")
with col_h:
    # Поле высоты БЕЗ key, обновляется через session_state
    height_input = st.number_input("Высота (мм)", min_value=MOD_H, step=MOD_H, value=st.session_state.height_mm)

# Синхронизация ручного ввода высоты в state
st.session_state.height_mm = height_input

# --- Панель быстрых пропорций ---
st.write("**Подгонка пропорций:**")
btn_cols = st.columns(4)

if btn_cols[0].button("16:9 (Широкоформатный)"):
    st.session_state.height_mm = round_to_mod((width_input / 16) * 9, MOD_H)
    st.rerun()
if btn_cols[1].button("4:3 (Классический)"):
    st.session_state.height_mm = round_to_mod((width_input / 4) * 3, MOD_H)
    st.rerun()
if btn_cols[2].button("21:9 (Кинематографичный)"):
    st.session_state.height_mm = round_to_mod((width_input / 21) * 9, MOD_H)
    st.rerun()
if btn_cols[3].button("1:1 (Квадрат)"):
    st.session_state.height_mm = round_to_mod(width_input, MOD_H)
    st.rerun()

# --- Популярные разрешения (предотвращение цикла через prev_popular) ---
popular_sizes = [
    "Не выбрано",
    "2560×1440", "3200×1800", "3840×2160", 
    "4120×2340", "4800×2700", "5120×2880", "6080×3420"
]
selected_popular = st.selectbox("Популярные размеры (16:9, Ш×В мм)", popular_sizes, key="pop_size")

if selected_popular != st.session_state.prev_popular:
    st.session_state.prev_popular = selected_popular
    if selected_popular != "Не выбрано":
        w_str, h_str = selected_popular.split("×")
        # Здесь мы не можем напрямую изменить width_key без rerun, 
        # но в Streamlit >= 1.28 можно менять key в session_state перед rerun
        st.session_state.width_key = int(w_str)
        st.session_state.height_mm = int(h_str)
        st.rerun()

st.markdown("---")

# --- Питание и резерв ---
col_psu1, col_psu2, col_psu3 = st.columns(3)
with col_psu1:
    psu_power = st.selectbox("Мощность БП (Mean Well)", ["200W", "300W", "400W"])
with col_psu2:
    psu_reserve_pct = st.selectbox("Запас по питанию", ["0%", "10%", "20%", "30%"], index=2)
with col_psu3:
    mod_reserve_pct = st.number_input("ЗИП модулей (%)", min_value=0, max_value=20, value=3)

# --- ВЫЧИСЛЕНИЯ (Автоматически после любого изменения) ---
w_mm = width_input
h_mm = st.session_state.height_mm

mod_cols = w_mm // MOD_W
mod_rows = h_mm // MOD_H
total_modules = mod_cols * mod_rows

area_m2 = (w_mm / 1000) * (h_mm / 1000)
res_w = int(w_mm / pixel_pitch)
res_h = int(h_mm / pixel_pitch)
total_pixels = res_w * res_h

# Питание
psu_cap_w = int(psu_power.replace("W", ""))
reserve_multiplier = 1 + (int(psu_reserve_pct.replace("%", "")) / 100.0)

# Примерная мощность модуля (зависит от Indoor/Outdoor)
mod_max_power = 25 if "Indoor" in env_type else 45 
total_peak_power = total_modules * mod_max_power
total_peak_power_with_reserve = total_peak_power * reserve_multiplier

# Количество БП (округление вверх)
total_psu = math.ceil(total_peak_power_with_reserve / psu_cap_w)
avg_power_kw = (total_peak_power * 0.35) / 1000 # Средняя мощность ~35% от пиковой
peak_power_kw = total_peak_power / 1000

# Ресиверные карты (грубый расчет: 1 карта на 256x256 пикселей для примера, или по кабинетам)
pixels_per_card = 256 * 256 
receiving_cards = max(1, math.ceil(total_pixels / pixels_per_card))

# ЗИП и вес
modules_zip = math.ceil(total_modules * (mod_reserve_pct / 100.0))
weight_per_m2 = 25 if "Монолитный" in cabinet_type else 35
total_weight = area_m2 * weight_per_m2
total_price = area_m2 * price_per_m2

# --- ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Площадь</div><div class="metric-value">{area_m2:.2f} м²</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Разрешение</div><div class="metric-value">{res_w} × {res_h}</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Пиковая мощность</div><div class="metric-value">{peak_power_kw:.1f} кВт</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Итоговая стоимость</div><div class="metric-value">{total_price:,.0f} ₽</div></div>', unsafe_allow_html=True)

# --- ДЕТАЛЬНЫЙ ОТЧЁТ (Expanders) ---
st.subheader("📋 Детализация комплектующих")

with st.expander("Модули и ЗИП", expanded=True):
    st.write(f"**Тип:** Qiangli {tech_type} P{pixel_pitch} {env_type}")
    st.write(f"**Сетка:** {mod_cols} шт (Ш) × {mod_rows} шт (В)")
    st.write(f"**Всего в экране:** {total_modules} шт.")
    st.write(f"**ЗИП (Резерв {mod_reserve_pct}%):** {modules_zip} шт.")
    st.write(f"**Итого к заказу:** {total_modules + modules_zip} шт.")
    st.write(f"**Магниты (для монолита):** {total_modules * 4} шт.")

with st.expander("Блоки питания (Mean Well)", expanded=False):
    st.write(f"**Модель:** Mean Well {psu_power}")
    st.write(f"**Запас надёжности:** {psu_reserve_pct}")
    st.write(f"**Количество БП:** {total_psu} шт.")
    st.write(f"**Среднее потребление:** {avg_power_kw:.2f} кВт/ч")

with st.expander("Система управления (Novastar)", expanded=False):
    st.write(f"**Процессор:** {processor} (Проверка портов: требуется {math.ceil(total_pixels/650000)} портов)")
    st.write(f"**Приёмные карты (Receiving Cards):** ~{receiving_cards} шт. (уточнить по схеме коммутации)")
    st.write(f"**Датчик яркости/температуры:** Опционально (Novastar NS060)")

with st.expander("Коммутация и Каркас", expanded=False):
    st.write("**Шлейфы данных:** В комплекте с модулями (по кол-ву модулей)")
    st.write(f"**Кабели питания 5V:** {math.ceil(total_modules / 2)} шт. (1 кабель на 2 модуля)")
    st.write(f"**Ориентировочный вес:** {total_weight:.1f} кг")
    st.write("**Упаковка:** Фанерные ящики или флайт-кейсы (рассчитывается индивидуально)")

# --- HTML СХЕМА (Для монолитного варианта) ---
if "Монолитный" in cabinet_type:
    st.subheader("📐 Схема сборки (Вид спереди)")
    
    # Генерация простой CSS Grid схемы
    html_grid = f"""
    <div style="
        display: grid; 
        grid-template-columns: repeat({mod_cols}, 1fr); 
        gap: 1px; 
        background-color: #4a5568; 
        padding: 2px;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
    ">
    """
    for _ in range(total_modules):
        html_grid += '<div style="background-color: #2d3748; aspect-ratio: 2/1; border: 1px solid #1a202c; display: flex; align-items: center; justify-content: center; font-size: 8px; color: #718096;">MOD</div>'
    html_grid += "</div>"
    
    st.components.v1.html(html_grid, height=int(800 * (mod_rows/mod_cols)) + 20)

st.markdown("---")

# --- ИНТЕГРАЦИИ: Figma JSON & Google Sheets ---
st.subheader("🔗 Экспорт и Интеграция")

# Формирование JSON для Figma Variables Studio
figma_data = {
    "project_name": project_name,
    "client": client_name,
    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "screen_dimensions_mm": f"{w_mm}x{h_mm}",
    "resolution_px": f"{res_w}x{res_h}",
    "area_m2": round(area_m2, 2),
    "pixel_pitch": pixel_pitch,
    "total_modules": total_modules,
    "modules_with_reserve": total_modules + modules_zip,
    "cabinet_type": cabinet_type,
    "receiving_cards": receiving_cards,
    "power_supplies": total_psu,
    "processor": processor,
    "peak_power_kw": round(peak_power_kw, 2),
    "avg_power_kw": round(avg_power_kw, 2),
    "power_reserve_percent": psu_reserve_pct,
    "total_weight_kg": round(total_weight, 1),
    "price_per_m2_rub": price_per_m2,
    "total_price_rub": total_price
}

figma_json = json.dumps(figma_data, indent=4, ensure_ascii=False)

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.markdown("**1. Экспорт в Figma**")
    st.write("Используйте этот JSON для вставки в Figma Variables Studio или сторонние плагины.")
    st.code(figma_json, language="json")
    # Streamlit не имеет встроенной кнопки копирования в буфер обмена без сторонних компонентов, 
    # но st.code имеет встроенную кнопку копирования при наведении.
    st.info("💡 Наведите на блок с кодом и нажмите иконку копирования в правом верхнем углу.")

with col_exp2:
    st.markdown("**2. Сохранение в Google Sheets**")
    st.write("Отправка текущего расчета в единую базу проектов (требуется Service Account).")
    
    if st.button("💾 Сохранить расчёт в Google Sheets"):
        try:
            # Попытка авторизации и записи (Работает если в st.secrets есть данные)
            if "google_sheets" in st.secrets:
                creds_dict = dict(st.secrets["google_sheets"])
                credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                client = gspread.authorize(credentials)
                
                # Замените 'LED_Calculations_DB' на реальное имя или ID вашей таблицы
                sheet = client.open("LED_Calculations_DB").sheet1
                
                row_to_insert = [
                    figma_data["date"],
                    figma_data["project_name"],
                    figma_data["client"],
                    figma_data["screen_dimensions_mm"],
                    figma_data["resolution_px"],
                    figma_data["area_m2"],
                    figma_data["pixel_pitch"],
                    figma_data["total_price_rub"]
                ]
                sheet.append_row(row_to_insert)
                st.success("✅ Данные успешно сохранены в Google Sheets!")
                st.markdown("[Перейти в таблицу](https://docs.google.com/spreadsheets/)")
            else:
                # Режим заглушки, если секретов нет
                st.warning("Внимание: Секреты `st.secrets['google_sheets']` не настроены.")
                st.success("✅ [Mock] Данные успешно сформированы для отправки в Google Sheets!")
                
        except Exception as e:
            st.error(f"❌ Ошибка сохранения: {e}")
            st.info("Проверьте наличие и правильность файла `.streamlit/secrets.toml`.")

# --- Инструкция по настройке Secrets (скрытая) ---
with st.expander("🛠 Инструкция по настройке Google Sheets Secrets"):
    st.markdown("""
    Для работы интеграции с Google Sheets создайте файл `.streamlit/secrets.toml` в корне вашего проекта и добавьте туда JSON вашего Service Account:
    ```toml
    [google_sheets]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "your-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_KEY\\n-----END PRIVATE KEY-----\\n"
    client_email = "your-email@your-project.iam.gserviceaccount.com"
    client_id = "your-client-id"
    auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
    token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
    auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
    client_x509_cert_url = "[https://www.googleapis.com/](https://www.googleapis.com/)..."
    ```
    Не забудьте дать доступ вашему `client_email` к Google Таблице (через кнопку "Поделиться" в самой таблице).
    """)
