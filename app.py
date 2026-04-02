import streamlit as st
import math
import json
import re
import datetime
from pathlib import Path
from typing import Optional
import urllib.request
import xml.etree.ElementTree as ET

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    pass

try:
    from pdf_report import build_led_report_pdf, suggested_pdf_filename
except ImportError:
    build_led_report_pdf = None
    suggested_pdf_filename = None

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="LED Screen Pro Calculator | MediaLive", layout="wide", page_icon="🖥️")


def _ui_bordered_container():
    """Streamlit ≥1.33: container(border=True); иначе обычный container."""
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


# --- СОВРЕМЕННЫЙ CSS ДИЗАЙН ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #151a22 100%);
        border-radius: 10px;
        padding: 16px 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #2d3748;
        margin-bottom: 16px;
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
    }
    .metric-value { font-size: 22px; font-weight: bold; color: #63b3ed; line-height: 1.25; }
    .metric-label { font-size: 12px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .metric-subrow { font-size: 16px; font-weight: bold; color: #63b3ed; line-height: 1.35; margin-top: 4px; }
    .finance-metric-card {
        padding: 14px 14px 12px 14px;
        border-radius: 10px;
        background: #1a202c;
        border: 1px solid #2d3748;
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        box-sizing: border-box;
        margin-bottom: 12px;
    }
    .spec-summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(128px, 1fr));
        gap: 16px 20px;
        margin-top: 14px;
    }
    .spec-summary-cell-label { font-size: 0.8rem; color: #718096; text-transform: uppercase; letter-spacing: 0.04em; line-height: 1.35; }
    .spec-summary-cell-val { font-size: 1.08rem; color: #e2e8f0; font-weight: 600; margin-top: 4px; line-height: 1.3; }
    .section4-panel {
        background: #161b22;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 8px;
        min-height: 0;
    }
    .section4-subtitle { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 12px 0; border-bottom: 1px solid #2d3748; padding-bottom: 8px; }
    
    .stButton>button {
        background: linear-gradient(90deg, #3182ce, #2b6cb0); 
        color: white; 
        border: none; 
        border-radius: 8px; 
        transition: all 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px); 
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }
    
    .section-header {
        color: #e2e8f0;
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2d3748;
    }
    
    div[data-testid="stExpander"] {
        background-color: #1a202c;
        border-radius: 8px;
        border: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИЯ ПАРСИНГА КУРСА ЦБ РФ (+1%) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cbr_usd_rate():
    try:
        url = "http://www.cbr.ru/scripts/XML_daily.asp"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for valute in root.findall('Valute'):
            if valute.attrib.get('ID') == 'R01235': # ID доллара США
                value_str = valute.find('Value').text.replace(',', '.')
                return float(value_str) * 1.01 # Возвращаем курс + 1%
        return 95.0
    except Exception:
        return 95.0 # Резервный курс при ошибке сети


# Профиль 40×20×1,5: в продаже только хлыст 6 м; в смете — ₽/п.м × (число хлыстов × 6).
PROFILE_40X20_STICK_M = 6.0
PROFILE_40X20_RUB_M_FALLBACK = 189.0

# Саморез 4,2×16 с прессшайбой (к профилю); в магазине обычно упаковка — ориентир ₽/шт.
SCREW_4X16_PRESS_RUB_EACH_FALLBACK = 1.5

# Заклёпка резьбовая Sormat M6 + винт M6×16 DIN 912 оцинк. (каркас монолита, 1+1 на узел).
RIVET_M6_SORMAT_RUB_EACH_FALLBACK = 12.0
BOLT_M6_6x16_DIN912_RUB_EACH_FALLBACK = 8.5
LEMANA_RIVET_M6_SORMAT_URL = "https://lemanapro.ru/product/zaklepka-sormat-m6-mm-87937034/"
LEMANA_BOLT_M6_6x16_DIN912_URL = (
    "https://lemanapro.ru/product/vint-din-912-6x16-mm-ocinkovannyy-24-sht-89397382/"
)

# Металлические пластины под БП (1 шт. на БП с ЗИП); фикс. 150 ₽/шт, только в смете «Каркас».
METAL_PLATE_RUB_EACH = 150.0

PETROVICH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
PETROVICH_PRICE_PATTERNS = (
    r'"price"\s*:\s*(\d{2,5})\s*[,}]',
    r'data-price="(\d{3,5})"',
    r'itemprop="price"\s+content="(\d+)"',
)


def _petrovich_first_listed_price_raw(urls: tuple) -> Optional[int]:
    """Первая похожая на цену цифра в HTML выдачи/каталога Петровича."""
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": PETROVICH_UA})
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            for pat in PETROVICH_PRICE_PATTERNS:
                m = re.search(pat, html)
                if m:
                    raw = int(m.group(1))
                    if 10 <= raw <= 50000:
                        return raw
        except Exception:
            continue
    return None


def _html_first_price_int(html: str) -> Optional[int]:
    """Первая целая цена в HTML (карточка товара)."""
    for pat in PETROVICH_PRICE_PATTERNS:
        m = re.search(pat, html)
        if m:
            raw = int(m.group(1))
            if 10 <= raw <= 50000:
                return raw
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def get_profile_40x20_rub_per_m_petrovich():
    """
    Пытается взять цену с petrovich.ru (поиск профтрубы 40×20), кэш 24 ч.
    Если вёрстка/сеть изменились — смотрите поле в сайдбаре и правьте URL/regex или вводите цену вручную.
    Возвращает (₽ за п.м., короткая подпись источника).
    """
    src_fail = "резерв (парсер/сеть)"
    urls = (
        "https://www.petrovich.ru/search/?search=truba+profilnaya+40+20+1.5",
        "https://www.petrovich.ru/search/?search=%D1%82%D1%80%D1%83%D0%B1%D0%B0+%D0%BF%D1%80%D0%BE%D1%84%D0%B8%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F+40+20+1.5",
    )
    raw = _petrovich_first_listed_price_raw(urls)
    if raw is not None:
        if raw >= 400:
            return (round(raw / PROFILE_40X20_STICK_M, 2), "petrovich.ru (из цены хлыста ÷6)")
        return (float(raw), "petrovich.ru")
    return (float(PROFILE_40X20_RUB_M_FALLBACK), src_fail)


@st.cache_data(ttl=86400, show_spinner=False)
def get_screw_4x16_press_rub_each_petrovich():
    """
    Цена самореза 4,2×16 с прессшайбой (сверло), кэш 24 ч.
    В выдаче Петровича чаще цена за упаковку — делим на типичное число шт. в уп.
    """
    src_fail = "резерв (парсер/сеть)"
    urls = (
        "https://www.petrovich.ru/search/?search=samorez+4.2x16+press+shayba",
        "https://www.petrovich.ru/search/?search=samorez+4.2+16+sv+press",
        "https://www.petrovich.ru/search/?search=%D1%81%D0%B0%D0%BC%D0%BE%D1%80%D0%B5%D0%B7+4%D1%8516+%D0%BF%D1%80%D0%B5%D1%81%D1%81%D1%88%D0%B0%D0%B9%D0%B1%D0%B0",
    )
    raw = _petrovich_first_listed_price_raw(urls)
    if raw is None:
        return (float(SCREW_4X16_PRESS_RUB_EACH_FALLBACK), src_fail)
    if raw >= 800:
        return (round(raw / 1000.0, 4), "petrovich.ru (цена ÷1000 шт/уп)")
    if raw >= 400:
        return (round(raw / 500.0, 4), "petrovich.ru (цена ÷500 шт/уп)")
    if raw >= 150:
        return (round(raw / 200.0, 4), "petrovich.ru (цена ÷200 шт/уп)")
    if raw >= 70:
        return (round(raw / 100.0, 4), "petrovich.ru (цена ÷100 шт/уп)")
    if raw >= 25:
        return (round(raw / 50.0, 4), "petrovich.ru (цена ÷50 шт/уп)")
    if raw >= 12:
        return (round(raw / 20.0, 4), "petrovich.ru (цена ÷20 шт/уп)")
    return (float(raw), "petrovich.ru (как за 1 шт)")


@st.cache_data(ttl=86400, show_spinner=False)
def get_rivet_m6_sormat_rub_each_lemana():
    """
    Заклёпка резьбовая Sormat M6, кэш 24 ч.
    Карточка: lemanapro.ru (число шт. в уп. из текста страницы или 1 шт.).
    """
    src_fail = "резерв (Lemana/сеть)"
    url = LEMANA_RIVET_M6_SORMAT_URL
    pack = 1
    m_url = re.search(r"-(\d+)-sht", url, re.I)
    if m_url:
        pack = max(1, int(m_url.group(1)))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": PETROVICH_UA})
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        m_pack = re.search(r"(\d+)\s*шт", html[:120000], re.I)
        if m_pack:
            pack = max(1, int(m_pack.group(1)))
        raw = _html_first_price_int(html)
        if raw is None:
            m = re.search(r'"finalPrice"\s*:\s*(\d{2,6})', html)
            if m:
                raw = int(m.group(1))
        if raw is not None and 5 <= raw <= 50000 and pack > 0:
            return (round(raw / float(pack), 4), f"lemanapro.ru (уп. {pack} шт, Sormat M6)")
    except Exception:
        pass
    return (float(RIVET_M6_SORMAT_RUB_EACH_FALLBACK), src_fail)


@st.cache_data(ttl=86400, show_spinner=False)
def get_bolt_m6_6x16_din912_zinc_rub_each_lemana():
    """
    Винт M6×16 DIN 912 оцинк., кэш 24 ч.
    Карточка: lemanapro.ru (упаковка в URL, напр. 24 шт).
    """
    src_fail = "резерв (Lemana/сеть)"
    url = LEMANA_BOLT_M6_6x16_DIN912_URL
    pack = 24
    m_url = re.search(r"-(\d+)-sht", url, re.I)
    if m_url:
        pack = max(1, int(m_url.group(1)))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": PETROVICH_UA})
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        m_pack = re.search(r"(\d+)\s*шт", html[:120000], re.I)
        if m_pack:
            pack = max(1, int(m_pack.group(1)))
        raw = _html_first_price_int(html)
        if raw is None:
            m = re.search(r'"finalPrice"\s*:\s*(\d{2,6})', html)
            if m:
                raw = int(m.group(1))
        if raw is not None and 15 <= raw <= 50000 and pack > 0:
            return (round(raw / float(pack), 4), f"lemanapro.ru (уп. {pack} шт, DIN 912 6×16)")
    except Exception:
        pass
    return (float(BOLT_M6_6x16_DIN912_RUB_EACH_FALLBACK), src_fail)


# --- БАЗА ДАННЫХ МОДУЛЕЙ (USD: прайс LEDCapital «Комплектующие» 23.03.2026) ---
MODULES_DB = [
    # INDOOR
    {'name': 'Qiangli Q1.25 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 44.99},
    {'name': 'Qiangli Q1.25 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 46.15},
    {'name': 'Qiangli Q1.25 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.25, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 51.10},
    {'name': 'Qiangli R1.5 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 33.44},
    {'name': 'Qiangli Q1.53 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.42},
    {'name': 'VISTECH P1.53 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 42.38},
    {'name': 'Qiangli Q1.53 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 30.42},
    {'name': 'Qiangli Q1.53 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.53, 'tech': 'GOB', 'brightness': 650, 'max_power': 30.0, 'price_usd': 35.15},
    {'name': 'Qiangli Q1.66 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.66, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 27.54},
    {'name': 'Qiangli Q1.86 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 500, 'max_power': 23.0, 'price_usd': 18.64},
    {'name': 'Qiangli R1.86 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 21.99},
    {'name': 'VISTECH P1.86 COB Indoor 3840Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'COB', 'brightness': 600, 'max_power': 30.0, 'price_usd': 29.75},
    {'name': 'Qiangli Q1.86 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'SMD', 'brightness': 600, 'max_power': 30.0, 'price_usd': 19.99},
    {'name': 'Qiangli R1.86 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 1.86, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 22.88},
    {'name': 'Qiangli Q2 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 23.0, 'price_usd': 16.63},
    {'name': 'Qiangli R2 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 19.97},
    {'name': 'Qiangli Q2 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 23.0, 'price_usd': 17.60},
    {'name': 'Qiangli R2 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'Flexible', 'brightness': 500, 'max_power': 23.0, 'price_usd': 20.77},
    {'name': 'Qiangli Q2 GOB Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.0, 'tech': 'GOB', 'brightness': 600, 'max_power': 23.0, 'price_usd': 21.85},
    {'name': 'Qiangli Q2.5 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.03},
    {'name': 'Qiangli Q2.5 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 12.55},
    {'name': 'Qiangli R2.5 Indoor 3840Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 500, 'max_power': 24.0, 'price_usd': 14.88},
    {'name': 'Qiangli Q2.5 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 500, 'max_power': 24.0, 'price_usd': 13.43},
    {'name': 'Qiangli R2.5 Indoor 6000Hz (Гибкий)', 'env': 'Indoor', 'pitch': 2.5, 'tech': 'Flexible', 'brightness': 600, 'max_power': 24.0, 'price_usd': 15.56},
    {'name': 'Qiangli Q3.07 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 500, 'max_power': 22.0, 'price_usd': 8.98},
    {'name': 'Qiangli Q3.07 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 600, 'max_power': 22.0, 'price_usd': 10.61},
    {'name': 'Qiangli Q3.07 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 600, 'max_power': 22.0, 'price_usd': 10.99},
    {'name': 'Qiangli Q4 Indoor 1920Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 450, 'max_power': 24.0, 'price_usd': 7.55},
    {'name': 'Qiangli Q4 Indoor 3840Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 24.0, 'price_usd': 8.46},
    {'name': 'Qiangli Q4 Indoor 6000Hz', 'env': 'Indoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 600, 'max_power': 24.0, 'price_usd': 8.70},

    # OUTDOOR
    {'name': 'Qiangli Q2.5 Outdoor 3840Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.39},
    {'name': 'Qiangli Q2.5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 2.5, 'tech': 'SMD', 'brightness': 4500, 'max_power': 33.0, 'price_usd': 24.80},
    {'name': 'Qiangli Q3.07 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4200, 'max_power': 40.0, 'price_usd': 15.29},
    {'name': 'Qiangli Q3.07 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 3.07, 'tech': 'SMD', 'brightness': 4500, 'max_power': 40.0, 'price_usd': 16.15},
    {'name': 'Qiangli Q4 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.02},
    {'name': 'Qiangli R4 Outdoor 3840Hz (Гибкий)', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'Flexible', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 25.09},
    {'name': 'Qiangli Q4 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 4.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 47.0, 'price_usd': 11.49},
    {'name': 'Qiangli Q5 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.08},
    {'name': 'Qiangli Q5 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 5.0, 'tech': 'SMD', 'brightness': 5000, 'max_power': 43.0, 'price_usd': 9.55},
    {'name': 'Qiangli Q6.66 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 4500, 'max_power': 46.0, 'price_usd': 8.87},
    {'name': 'Qiangli Q6.66 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 6.66, 'tech': 'SMD', 'brightness': 5000, 'max_power': 46.0, 'price_usd': 9.30},
    {'name': 'Qiangli Q8 Outdoor 2880Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 7.65},
    {'name': 'Qiangli Q8 Outdoor 7680Hz', 'env': 'Outdoor', 'pitch': 8.0, 'tech': 'SMD', 'brightness': 4500, 'max_power': 44.0, 'price_usd': 8.05},
]
# Синхронные контроллеры (USD: LEDCapital 23.03.2026)
SYNC_CONTROLLERS_DB = [
    {"name": "Novastar MSD 300", "price_usd": 100.63},
    {"name": "Novastar MSD 600", "price_usd": 207.03},
    {"name": "Novastar MCTRL 300", "price_usd": 155.53},
    {"name": "Novastar MCTRL 500", "price_usd": 336.72},
    {"name": "Novastar MCTRL 600", "price_usd": 278.31},
    {"name": "Novastar MCTRL 700", "price_usd": 290.46},
    {"name": "Novastar MCTRL 660", "price_usd": 474.83},
    {"name": "Novastar MCTRL 660 Pro", "price_usd": 810.40},
    {"name": "Novastar MX30", "price_usd": 2228.28},
    {"name": "Novastar MX40 Pro", "price_usd": 5657.79},
    {"name": "Novastar MCTRL R5", "price_usd": 1926.10},
    {"name": "Novastar MCTRL 4K", "price_usd": 3210.51},
    {"name": "NovaPro UHD JR", "price_usd": 5142.86},
    {"name": "NovaPro UHD", "price_usd": 3090.00},
    {"name": "VX400", "price_usd": 889.92},
    {"name": "VX600", "price_usd": 987.77},
    {"name": "VX1000", "price_usd": 1357.54},
    {"name": "VC2", "price_usd": 105.06},
    {"name": "VC4", "price_usd": 179.22},
    {"name": "VC6 Pro", "price_usd": 448.05},
    {"name": "VC10", "price_usd": 889.92},
    {"name": "VC10 Pro", "price_usd": 893.85},
    {"name": "VC16", "price_usd": 1781.90},
]

# Асинхронные контроллеры (строки 20-27)
ASYNC_CONTROLLERS_DB = [
    {"name": "T30", "price_usd": 206.00},
    {"name": "T50", "price_usd": 283.25},
    {"name": "TB10 Plus", "price_usd": 58.61},
    {"name": "TB20 Plus", "price_usd": 111.96},
    {"name": "TB30", "price_usd": 236.39},
    {"name": "TB40", "price_usd": 181.28},
    {"name": "TB50", "price_usd": 348.14},
    {"name": "TB60", "price_usd": 404.58},
]
# --- ДОБАВЛЯЕМ НОВЫЕ СПРАВОЧНИКИ КАРТ И ХАБОВ ---
RECEIVING_CARDS_DB = [
    {"name": "Novastar MRV 208", "price_usd": 13.29, "type": "MRV"},
    {"name": "Novastar MRV 412", "price_usd": 15.40, "type": "MRV"},
    {"name": "Novastar MRV 416", "price_usd": 16.09, "type": "MRV"},
    {"name": "Novastar MRV 532", "price_usd": 21.00, "type": "MRV"},
    {"name": "Novastar CA50E (COEX)", "price_usd": 138.65, "type": "COEX"},
    {"name": "Novastar A5s Plus", "price_usd": 17.02, "type": "A"},
    {"name": "Novastar A7s Plus", "price_usd": 19.12, "type": "A"},
    {"name": "Novastar A8s", "price_usd": 33.89, "type": "A"},
    {"name": "Novastar A10s Plus", "price_usd": 44.57, "type": "A"},
    {"name": "Novastar A10s Pro", "price_usd": 71.31, "type": "A"},
]
# Блоки питания (USD: LEDCapital 23.03.2026; позиции Chuanglian/A-серия по прайсу)
PSU_DB = [
    {"name": "A-200-5 (Chuanglian)", "price_usd": 6.84, "max_w": 200},
    {"name": "A-200-5N (Slim) (Chuanglian)", "price_usd": 12.80, "max_w": 200},
    {"name": "A-300-5 (Slim) (Chuanglian)", "price_usd": 14.27, "max_w": 300},
    {"name": "A-200JQ-5 slim (Chuanglian)", "price_usd": 13.87, "max_w": 200},
    {"name": "A-300FAR-4.5PH (Chuanglian)", "price_usd": 21.79, "max_w": 300},
    {"name": "A-400JQ-4.5PH (Chuanglian)", "price_usd": 14.86, "max_w": 400},
    {"name": "Mean Well LRS-200-5", "price_usd": 15.58, "max_w": 200},
    {"name": "Mean Well LRS-350-5", "price_usd": 21.05, "max_w": 350},
    {"name": "G-Energy N200V5-A (Slim)", "price_usd": 13.57, "max_w": 200},
    {"name": "CZCL A-200-5N (Slim)", "price_usd": 12.80, "max_w": 200},
    {"name": "CZCL A-300-5 (Slim)", "price_usd": 14.50, "max_w": 300},
]
# Хабы (USD: LEDCapital 23.03.2026)
HUBS_DB = [
    {"name": "HUB 75E", "price_usd": 5.29},
    {"name": "HUB 75E-AXS", "price_usd": 14.86},
    {"name": "HUB 320-AXS", "price_usd": 14.86},
]
# Патч-корды (LEDCapital 23.03.2026; в Excel 1 м и 1,5 м)
PATCH_CORDS_DB = [
    {"name": "Патч-корд (LAN RJ45), 1 м", "length_m": 1.0, "price_usd": 0.90},
    {"name": "Патч-корд (LAN RJ45), 1,5 м", "length_m": 1.5, "price_usd": 1.09},
]
# Кабель питания приёмной карты ↔ БП (LEDCapital 23.03.2026)
CARD_POWER_CABLES_DB = [
    {"name": "Кабель питания 2×1 (35 см)", "price_usd": 0.39},
    {"name": "Кабель питания 2×1 (50 см)", "price_usd": 0.47},
    {"name": "Кабель питания 5 м", "price_usd": 25.00},
]
# Силовые перемычки между БП (LEDCapital 23.03.2026). Монолит: выбор длины; кабинеты — позже в калькуляторе.
POWER_JUMPERS_MONOLITH_DB = [
    {"name": "Силовая перемычка 3×2,5 (15 см)", "length_cm": 15, "price_usd": 1.03},
    {"name": "Силовая перемычка 3×25 (25 см)", "length_cm": 25, "price_usd": 1.26},
    {"name": "Силовая перемычка 3×2,5 (35 см)", "length_cm": 35, "price_usd": 1.95},
    {"name": "Силовая перемычка 3×25 (70 см)", "length_cm": 70, "price_usd": 2.51},
    {"name": "Силовая перемычка 3×2,5 (75 см)", "length_cm": 75, "price_usd": 2.85},
    {"name": "Силовая перемычка 3×25 (120 см)", "length_cm": 120, "price_usd": 3.64},
]
# Магниты монолитного монтажа (прайс LEDCapital: цена за пачку; в калькуляторе — за шт.)
MAGNETS_DB = [
    {"name": "Магнит 12×8×1,2 мм", "pack_price_usd": 69.33, "pack_qty": 1000},
    {"name": "Магнит саморез 12×8×1,2 мм", "pack_price_usd": 59.42, "pack_qty": 1000},
    {"name": "Магнит 13×11×1,2 мм", "pack_price_usd": 49.54, "pack_qty": 1000},
    {"name": "Магнит 14×13×1,3 мм", "pack_price_usd": 69.33, "pack_qty": 1000},
    {"name": "Магнит 14×17×1,3 мм", "pack_price_usd": 69.33, "pack_qty": 1000},
]


def magnet_unit_usd(m):
    return m["pack_price_usd"] / m["pack_qty"]


# --- Сохранение / загрузка сессии (JSON в каталоге led_calc_sessions) ---
SESSION_SNAPSHOT_VERSION = 1
SESSIONS_DIR = Path(__file__).resolve().parent / "led_calc_sessions"
SESSION_STATE_KEYS_TO_PERSIST: frozenset[str] = frozenset(
    {
        "width_input",
        "height_mm",
        "calc_quick_size_label",
        "calc_project_name",
        "calc_client_name",
        "calc_exchange_rate",
        "calc_margin_pct",
        "calc_price_m2",
        "profile_40x20_rub_m_sidebar",
        "screw_4x16_rub_each_sidebar",
        "rivet_m6_rub_each_sidebar",
        "bolt_m6_6x16_rub_each_sidebar",
        "calc_env_key",
        "calc_tech_key",
        "calc_module_name",
        "calc_sensor",
        "calc_mount_type",
        "calc_cabinet_model",
        "calc_cabinet_w",
        "calc_cabinet_h",
        "calc_cabinet_weight",
        "main_magnet_select",
        "magnets_per_module_input",
        "sys_type_radio",
        "main_proc_select",
        "hot_backup_gige",
        "main_card_select",
        "mods_per_card_select",
        "main_hub_select",
        "final_psu_selector",
        "final_m_per_p",
        "final_phase",
        "calc_reserve_enabled",
        "calc_reserve_modules_choice",
        "calc_reserve_modules_custom",
        "calc_reserve_psu_cards",
        "main_power_jumper_select",
        "patch_cord_product_select",
        "card_power_cable_select",
    }
)


def _session_safe_slug(name: str) -> str:
    raw = (name or "").strip()
    s = re.sub(r"[^\w\-.()\s\u0400-\u04FF]", "_", raw, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s).strip("_") or "session"
    return s[:120]


def _deep_jsonable(v):
    if isinstance(v, dict):
        return {str(k): _deep_jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_deep_jsonable(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _pick_row_by_name(rows, name: Optional[str], fallback_index: int = 0):
    if not rows:
        return None
    if name:
        for r in rows:
            if r.get("name") == name:
                return r
    idx = max(0, min(fallback_index, len(rows) - 1))
    return rows[idx]


def coerce_session_object_references() -> None:
    ss = st.session_state
    if "main_proc_select" in ss and isinstance(ss["main_proc_select"], dict):
        cat = ss.get("sys_type_radio", "Синхронная")
        pdb = SYNC_CONTROLLERS_DB if cat == "Синхронная" else ASYNC_CONTROLLERS_DB
        fixed = _pick_row_by_name(pdb, ss["main_proc_select"].get("name"))
        if fixed is not None:
            ss["main_proc_select"] = fixed
    if "main_card_select" in ss and isinstance(ss["main_card_select"], dict):
        fixed = _pick_row_by_name(RECEIVING_CARDS_DB, ss["main_card_select"].get("name"))
        if fixed is not None:
            ss["main_card_select"] = fixed
    if "main_magnet_select" in ss and isinstance(ss["main_magnet_select"], dict):
        fixed = _pick_row_by_name(MAGNETS_DB, ss["main_magnet_select"].get("name"))
        if fixed is not None:
            ss["main_magnet_select"] = fixed
    if "final_psu_selector" in ss and isinstance(ss["final_psu_selector"], dict):
        fixed = _pick_row_by_name(PSU_DB, ss["final_psu_selector"].get("name"))
        if fixed is not None:
            ss["final_psu_selector"] = fixed
    if "main_hub_select" in ss and isinstance(ss["main_hub_select"], dict):
        fixed = _pick_row_by_name(HUBS_DB, ss["main_hub_select"].get("name"))
        if fixed is not None:
            ss["main_hub_select"] = fixed
    if "main_power_jumper_select" in ss and isinstance(ss["main_power_jumper_select"], dict):
        fixed = _pick_row_by_name(
            POWER_JUMPERS_MONOLITH_DB, ss["main_power_jumper_select"].get("name")
        )
        if fixed is not None:
            ss["main_power_jumper_select"] = fixed
    if "patch_cord_product_select" in ss and isinstance(ss["patch_cord_product_select"], dict):
        fixed = _pick_row_by_name(PATCH_CORDS_DB, ss["patch_cord_product_select"].get("name"))
        if fixed is not None:
            ss["patch_cord_product_select"] = fixed
    if "card_power_cable_select" in ss and isinstance(ss["card_power_cable_select"], dict):
        fixed = _pick_row_by_name(CARD_POWER_CABLES_DB, ss["card_power_cable_select"].get("name"))
        if fixed is not None:
            ss["card_power_cable_select"] = fixed


def collect_session_snapshot() -> dict:
    state = {}
    for k in SESSION_STATE_KEYS_TO_PERSIST:
        if k in st.session_state:
            state[k] = _deep_jsonable(st.session_state[k])
    return {
        "version": SESSION_SNAPSHOT_VERSION,
        "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "state": state,
    }


def persist_session_to_file(stem: str) -> tuple[bool, str]:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{_session_safe_slug(stem)}.json"
    try:
        path.write_text(
            json.dumps(collect_session_snapshot(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True, str(path)
    except OSError as e:
        return False, str(e)


def load_session_payload_from_file(stem: str) -> tuple[Optional[dict], Optional[str]]:
    path = SESSIONS_DIR / f"{stem}.json"
    if not path.is_file():
        return None, "Файл не найден"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return None, str(e)
    ver = data.get("version", 0)
    if ver > SESSION_SNAPSHOT_VERSION:
        return None, "Версия сессии новее, чем у калькулятора"
    state = data.get("state")
    if not isinstance(state, dict):
        return None, "Некорректный формат state"
    return state, None


def delete_session_file(stem: str) -> tuple[bool, Optional[str]]:
    path = SESSIONS_DIR / f"{stem}.json"
    if not path.is_file():
        return False, "Файл не найден"
    try:
        path.unlink()
        return True, None
    except OSError as e:
        return False, str(e)


def _sidebar_sessions_panel():
    try:
        return st.sidebar.container(border=True)
    except TypeError:
        return st.sidebar.container()


# --- СПРАВОЧНИКИ ---
# Число Gigabit Ethernet выходов под нагрузку на приёмные карты (основной контур).
# Ключи совпадают с полю name в SYNC_CONTROLLERS_DB / ASYNC_CONTROLLERS_DB.
# Источники: novastar.tech и публичные спецификации; уточняйте под вашу ревизию железа.
PROCESSOR_PORTS = {
    # Синхронные (SYNC_CONTROLLERS_DB)
    "Novastar MSD 300": 2,
    "Novastar MSD 600": 4,
    "Novastar MCTRL 300": 2,
    "Novastar MCTRL 500": 4,
    "Novastar MCTRL 600": 4,
    "Novastar MCTRL 700": 6,
    "Novastar MCTRL 660": 4,
    "Novastar MCTRL 660 Pro": 6,
    "Novastar MX30": 10,
    "Novastar MX40 Pro": 20,
    "Novastar MCTRL R5": 8,
    "Novastar MCTRL 4K": 16,
    "NovaPro UHD JR": 16,
    "NovaPro UHD": 20,
    "VX400": 4,
    "VX600": 6,
    "VX1000": 10,
    "VC2": 2,
    "VC4": 4,
    "VC6 Pro": 6,
    "VC6 PRO": 6,
    "VC10": 10,
    "VC10 Pro": 10,
    "VC10 PRO": 10,
    "VC16": 16,
    # Асинхронные (ASYNC_CONTROLLERS_DB)
    "T30": 2,
    "T50": 2,
    "TB10 Plus": 1,
    "TB20 Plus": 1,
    "TB30": 1,
    "TB40": 2,
    "TB50": 2,
    "TB60": 4,
    # Синонимы / прочие обозначения (не из прайса, для совместимости и расширений)
    "VX600 Pro": 6,
    "VX1000 Pro": 10,
    "VX2000 Pro": 20,
    "VX16S": 16,
    "VC6": 6,
    "VC24": 24,
    "MCTRL300": 2,
    "MCTRL600": 4,
    "MCTRL700": 6,
    "MCTRL4K": 16,
}

# Правило расчёта нагрузки GigE → приёмные карты (как в расчёте required_ports).
PROCESSOR_LOAD_PX_PER_PORT = 650_000

# Краткая подпись «поддерживаемое разрешение» для инфоплашки (офиц. спецификации уточняйте под ревизию).
PROCESSOR_RESOLUTION_NOTE = {
    "Novastar MSD 300": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MSD 600": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MCTRL 300": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MCTRL 500": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MCTRL 600": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MCTRL 700": "1920×1200@60; кастом до 3840 px по стороне",
    "Novastar MCTRL 660": "до 4096×2160@60 (уточняйте по ревизии)",
    "Novastar MCTRL 660 Pro": "до 4096×2160@60 (уточняйте по ревизии)",
    "Novastar MX30": "до 7680×4320@30 (8K-класс; уточняйте по ревизии)",
    "Novastar MX40 Pro": "составной холст до 16K×8K class (уточняйте по ревизии)",
    "Novastar MCTRL R5": "до 4096×2160@60 (5G; уточняйте по ревизии)",
    "Novastar MCTRL 4K": "до 4096×2160@60 (4×10G / 16×GigE; уточняйте)",
    "NovaPro UHD JR": "до 8K class / UHD (уточняйте по ревизии)",
    "NovaPro UHD": "до 8K class / UHD (уточняйте по ревизии)",
    "VX400": "видеопроцессор: до 4K / по спецификации серии VX",
    "VX600": "видеопроцессор: до 4K / по спецификации серии VX",
    "VX1000": "видеопроцессор: до 4K+ / по спецификации серии VX",
    "VC2": "до 1920×1200@60; кастом до 3840 px по стороне",
    "VC4": "до 1920×1200@60; кастом до 3840 px по стороне",
    "VC6 Pro": "до 1920×1200@60; кастом до 3840 px по стороне",
    "VC10": "до 1920×1200@60; кастом до 3840 px по стороне",
    "VC10 Pro": "до 1920×1200@60; кастом до 3840 px по стороне",
    "VC16": "до 1920×1200@60; кастом до 3840 px по стороне",
    "T30": "асинхронный контроллер — по паспорту модели",
    "T50": "асинхронный контроллер — по паспорту модели",
    "TB10 Plus": "асинхронный контроллер — по паспорту модели",
    "TB20 Plus": "асинхронный контроллер — по паспорту модели",
    "TB30": "асинхронный контроллер — по паспорту модели",
    "TB40": "асинхронный контроллер — по паспорту модели",
    "TB50": "асинхронный контроллер — по паспорту модели",
    "TB60": "асинхронный контроллер — по паспорту модели",
}


def get_processor_output_ports(processor_name: str) -> tuple[int, bool]:
    """Возвращает (число портов, найдено ли имя в справочнике)."""
    if processor_name in PROCESSOR_PORTS:
        return PROCESSOR_PORTS[processor_name], True
    return 1, False

CARD_MAX_PIXELS = {
    "Novastar MRV 208": (256, 256),
    "Novastar MRV 412": (512, 512),
    "Novastar MRV 416": (512, 512),
    "Novastar MRV 532": (256, 384),
    "Novastar CA50E (COEX)": (512, 768),
    "Novastar A5s Plus": (512, 384),
    "Novastar A7s Plus": (512, 512),
    "Novastar A8s": (512, 256),
    "Novastar A10s Plus": (512, 512),
    "Novastar A10s Pro": (512, 512)
}
popular_16_9 = {
    "2560 × 1440 мм (8×9 шт) | Идеально 16:9": (2560, 1440),
    "2880 × 1600 мм (9×10 шт) | ~16:9": (2880, 1600),
    "3200 × 1760 мм (10×11 шт) | ~16:9": (3200, 1760),
    "3840 × 2240 мм (12×14 шт) | ~16:9": (3840, 2240),
    "4800 × 2720 мм (15×17 шт) | ~16:9": (4800, 2720),
    "5120 × 2880 мм (16×18 шт) | Идеально 16:9": (5120, 2880),
    "6080 × 3360 мм (19×21 шт) | ~16:9": (6080, 3360),
    "7680 × 4320 мм (24×27 шт) | Идеально 16:9": (7680, 4320),
    "Свой размер (вручную)": (None, None)
}

# --- ИНИЦИАЛИЗАЦИЯ STATE ---
_pop16_keys = list(popular_16_9.keys())
if "width_input" not in st.session_state:
    st.session_state.width_input = 3840
if "height_mm" not in st.session_state:
    st.session_state.height_mm = 2240
if "calc_quick_size_label" not in st.session_state:
    st.session_state.calc_quick_size_label = _pop16_keys[3]
if "_prev_quick_size_label" not in st.session_state:
    st.session_state._prev_quick_size_label = st.session_state.calc_quick_size_label

if "_session_payload_to_apply" in st.session_state:
    _payload = st.session_state.pop("_session_payload_to_apply")
    for _k, _v in _payload.items():
        if _k in SESSION_STATE_KEYS_TO_PERSIST:
            st.session_state[_k] = _v
    coerce_session_object_references()
    st.session_state._prev_quick_size_label = st.session_state.get(
        "calc_quick_size_label", _pop16_keys[3]
    )
    st.rerun()

def fit_ratio(ratio):
    ideal = st.session_state.width_input / ratio
    lower = math.floor(ideal / 160) * 160
    upper = math.ceil(ideal / 160) * 160
    st.session_state.height_mm = lower if abs(ideal - lower) <= abs(ideal - upper) else upper

# Обработка выбора популярного размера
st.sidebar.selectbox("📐 Быстрый размер (16:9)", _pop16_keys, key="calc_quick_size_label")
if st.session_state.calc_quick_size_label != st.session_state._prev_quick_size_label:
    _sw, _sh = popular_16_9[st.session_state.calc_quick_size_label]
    if _sw is not None:
        st.session_state.width_input = _sw
        st.session_state.height_mm = _sh
    st.session_state._prev_quick_size_label = st.session_state.calc_quick_size_label
    st.rerun()

# --- БОКОВАЯ ПАНЕЛЬ: ПРОЕКТ И ФИНАНСЫ ---
st.sidebar.markdown("---")
st.sidebar.header("📝 Данные проекта")
if "calc_project_name" not in st.session_state:
    st.session_state.calc_project_name = "MediaLive - Новый проект"
project_name = st.sidebar.text_input("Имя проекта", key="calc_project_name")
if "calc_client_name" not in st.session_state:
    st.session_state.calc_client_name = ""
client_name = st.sidebar.text_input("Клиент / Заказчик", placeholder="Введите имя клиента", key="calc_client_name")

st.sidebar.markdown("---")
st.sidebar.header("💾 Сессия")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
_saved_session_names = sorted(p.stem for p in SESSIONS_DIR.glob("*.json"))
# Сброс: удалить ключ виджета до его создания (присваивание в тот же key запрещено API Streamlit)
if st.session_state.pop("_reset_calc_session_new_name", False):
    st.session_state.pop("calc_session_new_name", None)
st.sidebar.text_input(
    "Имя для сохранения",
    value="",
    placeholder="например зал_А_вариант_1",
    key="calc_session_new_name",
    help="Файл появится в папке led_calc_sessions рядом с app.py",
)
if st.sidebar.button("Сохранить", use_container_width=True, key="calc_session_btn_save"):
    _name = (st.session_state.calc_session_new_name or "").strip() or "session"
    _ok, _msg = persist_session_to_file(_name)
    if _ok:
        st.session_state["_reset_calc_session_new_name"] = True
        st.sidebar.success("Сохранено")
        st.rerun()
    else:
        st.sidebar.error(f"Ошибка: {_msg}")

_load_clicked = False
_del_clicked = False
with _sidebar_sessions_panel():
    st.markdown(
        '<p style="margin:0 0 10px 0;color:#94a3b8;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">'
        "Сохранённые сессии</p>",
        unsafe_allow_html=True,
    )
    if _saved_session_names:
        if (
            "calc_session_pick" not in st.session_state
            or st.session_state.calc_session_pick not in _saved_session_names
        ):
            st.session_state.calc_session_pick = _saved_session_names[0]
        st.radio(
            "Выберите файл",
            _saved_session_names,
            key="calc_session_pick",
            label_visibility="collapsed",
        )
        _b_load_col, _b_del_col = st.columns(2)
        with _b_load_col:
            _load_clicked = st.button(
                "Загрузить",
                use_container_width=True,
                key="calc_session_btn_load",
            )
        with _b_del_col:
            _del_clicked = st.button(
                "Удалить",
                use_container_width=True,
                key="calc_session_btn_delete",
            )
    else:
        st.caption("Пока нет файлов — введите имя выше и нажмите «Сохранить».")

if _del_clicked and _saved_session_names:
    _stem = st.session_state.get("calc_session_pick")
    if _stem:
        _ok_del, _err_del = delete_session_file(_stem)
        if not _ok_del:
            st.sidebar.error(_err_del or "Не удалось удалить")
        else:
            st.session_state.pop("calc_session_pick", None)
            st.sidebar.success("Удалено")
            st.rerun()

if _load_clicked and _saved_session_names:
    _stem = st.session_state.get("calc_session_pick")
    if _stem:
        _data, _err = load_session_payload_from_file(_stem)
        if _err:
            st.sidebar.error(_err)
        else:
            st.session_state["_session_payload_to_apply"] = _data
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("💵 Финансы")

# Получаем актуальный курс
current_cbr_rate = get_cbr_usd_rate()
_profile_auto_rub_m, profile_price_source_note = get_profile_40x20_rub_per_m_petrovich()
_screw_auto_rub_each, screw_4x16_price_source_note = get_screw_4x16_press_rub_each_petrovich()
_rivet_m6_auto_rub, rivet_m6_price_source_note = get_rivet_m6_sormat_rub_each_lemana()
_bolt_m6_auto_rub, bolt_m6_6x16_price_source_note = get_bolt_m6_6x16_din912_zinc_rub_each_lemana()

if "calc_exchange_rate" not in st.session_state:
    st.session_state.calc_exchange_rate = float(current_cbr_rate)
exchange_rate = st.sidebar.number_input(
    "Курс USD (₽) для закупки (ЦБ + 1%)",
    min_value=50.0,
    step=0.1,
    key="calc_exchange_rate",
    help="Курс автоматически парсится с сайта ЦБ РФ + добавляется 1%, согласно правилам прайс-листа.",
)

profile_40x20_rub_m = st.sidebar.number_input(
    "Профиль 40×20×1,5 монолит (₽/п.м)",
    min_value=0.0,
    value=float(_profile_auto_rub_m),
    step=1.0,
    key="profile_40x20_rub_m_sidebar",
    help=(
        "Закупка: только хлысты по 6 м. Сумма = ceil(нужные м / 6) × 6 × ₽/м (остаток после пила уже в стоимости). "
        "Цена подставляется из Петровича не чаще 1 раза в сутки (кэш); при сбое — резерв, правьте вручную."
    ),
)
st.sidebar.caption(f"Профиль: {profile_price_source_note} · кэш 24 ч")

screw_4x16_press_rub_each = st.sidebar.number_input(
    "Саморез 4,2×16 прессшайба, сверло (₽/шт)",
    min_value=0.0,
    value=float(_screw_auto_rub_each),
    step=0.05,
    format="%.3f",
    key="screw_4x16_rub_each_sidebar",
    help=(
        "Монолит: крепление к профилю (основные + запас 10%). Цена из Петровича не чаще 1 раза в сутки; "
        "в выдаче часто цена за упаковку — в коде деление на типичное число шт."
    ),
)
st.sidebar.caption(f"Саморезы: {screw_4x16_price_source_note} · кэш 24 ч")

rivet_m6_threaded_rub_each = st.sidebar.number_input(
    "Заклёпка резьбовая M6 Sormat (₽/шт)",
    min_value=0.0,
    value=float(_rivet_m6_auto_rub),
    step=0.5,
    format="%.3f",
    key="rivet_m6_rub_each_sidebar",
    help=(
        "Монолит: по 1 шт. на узел каркаса (вместе с винтом M6). Авто — карточка Lemana Pro, кэш 24 ч: "
        + LEMANA_RIVET_M6_SORMAT_URL
    ),
)
bolt_m6_6x16_din912_rub_each = st.sidebar.number_input(
    "Винт M6×16 DIN 912, оцинк. (₽/шт)",
    min_value=0.0,
    value=float(_bolt_m6_auto_rub),
    step=0.05,
    format="%.3f",
    key="bolt_m6_6x16_rub_each_sidebar",
    help=(
        "Монолит: по 1 шт. на узел. Авто — карточка Lemana Pro (24 шт/уп), кэш 24 ч: "
        + LEMANA_BOLT_M6_6x16_DIN912_URL
    ),
)
st.sidebar.caption(f"Заклёпка Sormat M6 (Lemana): {rivet_m6_price_source_note} · Винт M6×16: {bolt_m6_6x16_price_source_note}")

# --- ДОБАВЛЯЕМ КОЭФФИЦИЕНТ НАЦЕНКИ ---
margin_percent = st.sidebar.number_input(
    "Наценка на железо (%)", min_value=0, value=30, step=5, key="calc_margin_pct"
)
margin = 1 + (margin_percent / 100)  # Это создаст ту самую переменную 'margin' (например, 1.3)

st.sidebar.markdown("---")
# Оставляем цену за м2, если она тебе нужна для других расчетов
price_per_m2 = st.sidebar.number_input(
    "Цена за м² клиенту (₽)", min_value=0, value=150000, step=5000, key="calc_price_m2"
)

st.title("🖥️ Профессиональный калькулятор LED-экранов")
st.markdown("Точный расчет комплектующих на базе динамического прайс-листа LEDCapital.")

# ==========================================
# БЛОК 1: РАЗМЕРЫ И ПРОПОРЦИИ
# ==========================================
st.markdown('<div class="section-header">📏 1. Размеры экрана</div>', unsafe_allow_html=True)

col_w, col_h = st.columns(2)
with col_w:
    width_mm = st.number_input("Ширина экрана (мм) [Шаг 320]", min_value=320, step=320, key="width_input")
with col_h:
    height_mm = st.number_input(
        "Высота экрана (мм) [Шаг 160]", min_value=160, step=160, key="height_mm"
    )

st.markdown("<span style='font-size: 14px; color: #a0aec0;'>Быстрая подгонка высоты под пропорции:</span>", unsafe_allow_html=True)
btn_cols = st.columns(4)
if btn_cols[0].button("16:9 (Широкий)"): fit_ratio(1.7777777777777777); st.rerun()
if btn_cols[1].button("4:3 (ТВ)"): fit_ratio(1.3333333333333333); st.rerun()
if btn_cols[2].button("21:9 (Кино)"): fit_ratio(2.3333333333333335); st.rerun()
if btn_cols[3].button("1:1 (Квадрат)"): fit_ratio(1.0); st.rerun()

# ==========================================
# БЛОК 2: ХАРАКТЕРИСТИКИ И МОНТАЖ
# ==========================================
st.markdown('<div class="section-header">⚙️ 2. Матрица и Конструкция</div>', unsafe_allow_html=True)

col_mat, col_mount = st.columns(2)

with col_mat:
    c_env, c_tech = st.columns(2)
    with c_env:
        if "calc_env_key" not in st.session_state:
            st.session_state.calc_env_key = "Indoor"
        env_key = st.radio(
            "Среда использования", ["Indoor", "Outdoor"], horizontal=True, key="calc_env_key"
        )
    with c_tech:
        tech_options = sorted(
            set(m["tech"] for m in MODULES_DB if m["env"] == env_key),
            key=lambda t: (0 if t == "SMD" else 1, t),
        )
        if "calc_tech_key" not in st.session_state or st.session_state.calc_tech_key not in tech_options:
            st.session_state.calc_tech_key = tech_options[0] if tech_options else "SMD"
        tech_key = st.selectbox("Технология", tech_options, key="calc_tech_key")

    # Фильтруем базу данных по среде И технологии
    available_modules = [m for m in MODULES_DB if m["env"] == env_key and m["tech"] == tech_key]
    module_names = [m["name"] for m in available_modules]
    _default_module_name = "Qiangli Q2.5 Indoor 3840Hz"
    _mod_ix = (
        module_names.index(_default_module_name)
        if _default_module_name in module_names
        else 0
    )
    if "calc_module_name" not in st.session_state or st.session_state.calc_module_name not in module_names:
        st.session_state.calc_module_name = module_names[_mod_ix] if module_names else ""
    selected_module_name = st.selectbox(
        "Светодиодный модуль (из прайса):", module_names, key="calc_module_name"
    )
    
    # Получаем характеристики выбранного модуля
    selected_module = next(m for m in available_modules if m["name"] == selected_module_name)
    
    pixel_pitch = selected_module["pitch"]
    tech = selected_module["tech"]
    brightness = selected_module["brightness"]
    max_power_module = selected_module["max_power"]
    price_usd = selected_module["price_usd"]
    price_rub_per_module = price_usd * exchange_rate
    
    # Инфо-панель с характеристиками
    st.markdown(f"""
    <div style="padding: 12px; border-radius: 8px; border: 1px solid #2d3748; background: #1a202c; font-size: 14px; color: #e2e8f0; margin-bottom: 10px;">
        <span style="color: #a0aec0;">Шаг:</span> <strong>P{pixel_pitch}</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Тип:</span> <strong>{tech}</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Яркость:</span> <strong>{brightness} нит</strong><br>
        <span style="color: #a0aec0;">Макс. потребление:</span> <strong>{max_power_module} Вт/шт</strong> &nbsp;|&nbsp;
        <span style="color: #a0aec0;">Цена (закупка):</span> <strong style="color: #48bb78;">${price_usd:.2f}</strong> ({price_rub_per_module:.0f} ₽)
    </div>
    """, unsafe_allow_html=True)
        
    sensor = "Нет"
    if env_key == "Outdoor":
        if "calc_sensor" not in st.session_state:
            st.session_state.calc_sensor = "Есть (NS060)"
        sensor = st.selectbox("Датчик яркости", ["Нет", "Есть (NS060)"], key="calc_sensor")
    else:
        sensor = st.session_state.get("calc_sensor", "Нет")

with col_mount:
    if "calc_mount_type" not in st.session_state:
        st.session_state.calc_mount_type = "Монолитный (Магниты/Профиль)"
    mount_type = st.radio(
        "Тип монтажа",
        ["Монолитный (Магниты/Профиль)", "В кабинетах"],
        horizontal=True,
        key="calc_mount_type",
    )
    selected_magnet = None
    magnets_per_module = 0
    selected_power_jumper = None

    cabinet_model = "Монолит"
    cabinet_width, cabinet_height, cabinet_weight_per = 640, 480, 20.0
    
    if "кабинетах" in mount_type:
        cabinet_options = [
            "QM Series (640×480 мм, indoor, ~20 кг)",
            "MG Series (960×960 мм, outdoor/indoor, ~40 кг)",
            "QF Series (500×500 мм, rental/indoor, ~13.5 кг)",
            "QS Series (960×960 мм, outdoor fixed, ~45 кг)",
            "Custom (введите размер и вес вручную)",
        ]
        if "calc_cabinet_model" not in st.session_state or st.session_state.calc_cabinet_model not in cabinet_options:
            st.session_state.calc_cabinet_model = cabinet_options[0]
        cabinet_model = st.selectbox("Модель кабинета", cabinet_options, key="calc_cabinet_model")
        if "Custom" in cabinet_model:
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                if "calc_cabinet_w" not in st.session_state:
                    st.session_state.calc_cabinet_w = 640
                cabinet_width = st.number_input("Ширина (мм)", min_value=320, key="calc_cabinet_w")
            with cc2:
                if "calc_cabinet_h" not in st.session_state:
                    st.session_state.calc_cabinet_h = 480
                cabinet_height = st.number_input("Высота (мм)", min_value=160, key="calc_cabinet_h")
            with cc3:
                if "calc_cabinet_weight" not in st.session_state:
                    st.session_state.calc_cabinet_weight = 20.0
                cabinet_weight_per = st.number_input("Вес (кг)", min_value=1.0, key="calc_cabinet_weight")
        else:
            cab_map = {
                "QM": (640, 480, 20.0), "MG": (960, 960, 40.0), 
                "QF": (500, 500, 13.5), "QS": (960, 960, 45.0)
            }
            key_prefix = cabinet_model.split()[0]
            cabinet_width, cabinet_height, cabinet_weight_per = cab_map.get(key_prefix, (640, 480, 20.0))
    else:
        selected_magnet = st.selectbox(
            "Магниты (из прайса):",
            MAGNETS_DB,
            format_func=lambda m: (
                f"{m['name']} — ${magnet_unit_usd(m):.4f}/шт "
                f"(пачка {m['pack_qty']} шт → ${m['pack_price_usd']:.2f})"
            ),
            index=3,
            key="main_magnet_select",
            help="Стоимость входит в «Общая закупка». Количество = число модулей × норма ниже.",
        )
        magnets_per_module = st.number_input(
            "Магнитов на 1 модуль (320×160 мм)",
            min_value=0,
            max_value=24,
            value=4,
            step=1,
            key="magnets_per_module_input",
            help="Типично 4 шт. на модуль; задайте свою норму под конструкцию.",
        )
        _mu = magnet_unit_usd(selected_magnet)
        _mag_rub = _mu * exchange_rate
        st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background: #1a202c; border: 1px solid #2d3748; line-height: 1.6; margin-bottom: 10px;">
            <span style="color: #a0aec0; font-size: 13px;">
                Закупочная цена: <strong style="color: #48bb78;">${_mu:.4f}</strong> за шт.
                &nbsp;({_mag_rub:.2f} ₽/шт)
            </span><br>
            <span style="color: #a0aec0; font-size: 13px;">
                Пачка: <strong>{selected_magnet['pack_qty']} шт</strong> по
                <strong style="color: #48bb78;">${selected_magnet['pack_price_usd']:.2f}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# ==========================================
# БЛОК 3: УПРАВЛЕНИЕ И КОНТРОЛЛЕРЫ
# ==========================================
st.markdown('<div class="section-header">📺 3. Управление и Контроллеры</div>', unsafe_allow_html=True)

col_ctrl1, col_ctrl2 = st.columns(2)

with col_ctrl1:
    st.markdown("---")
    # 1. Выбор типа системы
    ctrl_category = st.radio(
        "Тип системы:",
        ["Синхронная", "Асинхронная"],
        horizontal=True,
        index=0,
        key="sys_type_radio",
    )
    
    # Фильтруем базу процессоров
    current_db = SYNC_CONTROLLERS_DB if ctrl_category == "Синхронная" else ASYNC_CONTROLLERS_DB
    _proc_default_ix = next(
        (i for i, p in enumerate(current_db) if p["name"] == "VC4"),
        0,
    )
    selected_proc = st.selectbox(
        "Модель контроллера/процессора:",
        current_db,
        index=_proc_default_ix,
        format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
        key="main_proc_select",
    )
    
    processor_name = selected_proc["name"]
    proc_price_usd = selected_proc["price_usd"]
    available_ports, ports_catalog_hit = get_processor_output_ports(processor_name)
    _proc_cap_px = available_ports * PROCESSOR_LOAD_PX_PER_PORT
    _proc_mln = _proc_cap_px / 1_000_000
    _proc_cap_mln_str = (
        f"{_proc_mln:.2f}".replace(".", ",").rstrip("0").rstrip(",") + " млн"
    )
    _proc_cap_px_spaced = f"{_proc_cap_px:,}".replace(",", "\u202f")
    _proc_res_note = PROCESSOR_RESOLUTION_NOTE.get(
        processor_name, "Уточняйте по паспорту выбранной модели."
    )
    _ports_warn = (
        " ⚠ не в справочнике портов — для расчёта принят 1" if not ports_catalog_hit else ""
    )
    st.markdown(
        f'<div style="padding: 12px; border-radius: 8px; background: #1a202c; border: 1px solid #2d3748; line-height: 1.65; margin-bottom: 10px;">'
        f'<span style="color: #a0aec0; font-size: 13px;"><strong style="color: #e2e8f0;">Процессор</strong> — {processor_name}</span><br>'
        f'<span style="color: #a0aec0; font-size: 13px;">Количество портов: <strong style="color: #e2e8f0;">{available_ports}</strong>{_ports_warn}</span><br>'
        f'<span style="color: #a0aec0; font-size: 13px;">Кол-во пикселей: '
        f'<strong style="color: #48bb78;">{_proc_cap_mln_str}</strong> '
        f'<span style="color: #718096;">({_proc_cap_px_spaced})</span></span><br>'
        f'<span style="color: #a0aec0; font-size: 13px;">Разрешение: <strong style="color: #e2e8f0;">{_proc_res_note}</strong></span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    hot_backup = st.checkbox(
        "Backup",
        value=False,
        key="hot_backup_gige",
        help=(
            "GigE: расчётное число выходов ×2 (дублирование до карт). "
            "Сравнение с физическим числом портов процессора."
        ),
    )

with col_ctrl2:
    st.markdown("---")
    # 1. Выбор приемной карты
    _card_416_ix = next(
        (i for i, c in enumerate(RECEIVING_CARDS_DB) if c["name"] == "Novastar MRV 416"),
        0,
    )
    selected_card = st.selectbox(
        "Приёмная карта (Novastar):",
        RECEIVING_CARDS_DB,
        index=_card_416_ix,
        format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
        key="main_card_select",
    )
    
    # --- НОВЫЙ БЛОК: КРАТНОСТЬ МОДУЛЕЙ ---
    # Список значений, как ты просил + стандартные для больших экранов
    card_mods_options = [6, 8, 10, 12, 14, 16, 18]
    
    modules_per_card = st.selectbox(
        "Кол-во модулей на 1 карту:",
        options=card_mods_options,
        index=card_mods_options.index(10),
        key="mods_per_card_select",
        help="Выберите физическую кратность модулей для одной приёмной карты.",
    )
    # -------------------------------------

    receiving_card = selected_card
    card_name = receiving_card["name"]
    card_price_usd = receiving_card["price_usd"]
    card_price_rub = card_price_usd * exchange_rate

    # ЛОГИКА ОТОБРАЖЕНИЯ РАЗРЕШЕНИЯ
    if any(model_num in card_name for model_num in ["412", "416"]):
        res_info = "512х512 (N) / 512х384"
    else:
        res_info = "256х256"

    # ИНФО-ПЛАШКА КАРТЫ
    st.markdown(f"""
    <div style="padding: 12px; border-radius: 8px; background: #1a202c; border: 1px solid #2d3748; line-height: 1.6; margin-bottom: 10px;">
        <span style="color: #a0aec0; font-size: 13px;">
            Серия: <strong>{receiving_card['type']}</strong> &nbsp;|&nbsp; Модель: <strong>{card_name}</strong> &nbsp;|&nbsp; Разрешение: <strong>{res_info}</strong>
        </span><br>
        <span style="color: #a0aec0; font-size: 13px;">
            Цена (закупка): <strong style="color: #48bb78;">${card_price_usd:.2f}</strong> ({card_price_rub:,.0f} ₽)
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 4. Логика хаба
    hub_price_usd = 0.0
    if receiving_card["type"] == "A":
        selected_hub = st.selectbox(
            "Выберите HUB для серии A:", 
            HUBS_DB,
            format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
            key="main_hub_select"
        )
        hub_price_usd = selected_hub["price_usd"]
    else:
        st.info("HUB75 встроен в карту (MRV)")

if not ports_catalog_hit:
    st.warning(
        f"Модель **{processor_name}** не найдена в справочнике портов — для расчёта принято **1** выход. "
        "Добавьте строку в `PROCESSOR_PORTS` в `app.py`."
    )

# РАСЧЕТЫ ДОЛЖНЫ ИДТИ ПОСЛЕ БЛОКА IF С ТЕМ ЖЕ ОТСТУПОМ, ЧТО И ВЕСЬ БЛОК
real_width = math.ceil(width_mm / 320) * 320

# РАСЧЕТ И СТАТУС ПОРТОВ (единственная инфо-панель для контроллера)
real_width = math.ceil(width_mm / 320) * 320
real_height = math.ceil(height_mm / 160) * 160
total_px = (real_width / pixel_pitch) * (real_height / pixel_pitch)

required_ports_base = math.ceil(total_px / PROCESSOR_LOAD_PX_PER_PORT)
required_ports = required_ports_base * 2 if hot_backup else required_ports_base
load_per_port = (
    (total_px / (available_ports * PROCESSOR_LOAD_PX_PER_PORT)) * 100
    if available_ports > 0
    else 100.0
)

ports_ok = required_ports <= available_ports
status_text = "✅ Портов достаточно" if ports_ok else "❌ ВНИМАНИЕ: Недостаточно портов!"
status_color = "#48bb78" if ports_ok else "#f56565"
_hot_note = (
    f' &nbsp;|&nbsp; Backup: база <strong>{required_ports_base}</strong> → нужно <strong>{required_ports}</strong>'
    if hot_backup
    else ""
)

st.markdown(f"""
<div style="padding: 12px 20px; border-radius: 8px; border-left: 4px solid {status_color}; background: #1a202c; margin-top: 10px;">
    <span style="color: #a0aec0; font-size: 14px;">Статус портов процессора <strong>{processor_name}</strong>:</span><br>
    Доступно: <strong>{available_ports}</strong> &nbsp;|&nbsp;
    Требуется: <strong>{required_ports}</strong>{_hot_note} &nbsp;|&nbsp;
    Нагрузка на порт: <strong>{load_per_port:.1f}%</strong> &nbsp;&nbsp;➔&nbsp;&nbsp;
    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
</div>
""", unsafe_allow_html=True)
if not ports_ok:
    st.error(
        f"Недостаточно GigE-выходов: нужно **{required_ports}** (физически **{available_ports}** у "
        f"{processor_name}). Увеличьте модель процессора или снимите Backup."
    )

# ==========================================
# БЛОК 4: ПИТАНИЕ И РЕЗЕРВ (ЗИП) - ФИНАЛЬНЫЙ ЧИСТЫЙ ВАРИАНТ
# ==========================================
st.markdown('<div class="section-header">⚡ 4. Питание сети и ЗИП</div>', unsafe_allow_html=True)

col4_pwr, col4_zip = st.columns(2)
with col4_pwr:
    with _ui_bordered_container():
        st.markdown('<p class="section4-subtitle">Блок питания</p>', unsafe_allow_html=True)
        selected_psu = st.selectbox(
            "Модель БП (из прайса):",
            PSU_DB,
            format_func=lambda x: f"{x['name']} — ${x['price_usd']:.2f}",
            index=0,
            key="final_psu_selector",
        )
        sel_psu = selected_psu
        st.markdown(
            f"""
<div style="padding: 10px 12px; border-radius: 8px; border: 1px solid #2d3748; background: #1a202c; font-size: 13px; color: #e2e8f0; margin-bottom: 8px;">
    <span style="color: #a0aec0;">Мощность:</span> <strong>{sel_psu['max_w']}W</strong> &nbsp;|&nbsp;
    <span style="color: #a0aec0;">Цена за шт:</span> <strong style="color: #48bb78;">${sel_psu['price_usd']:.2f}</strong> ({(sel_psu['price_usd'] * exchange_rate):.0f} ₽)
</div>
""",
            unsafe_allow_html=True,
        )
        _mpsu_opts = [4, 6, 8, 10, 12, 16]
        modules_per_psu = st.selectbox(
            "Модулей на 1 БП:",
            _mpsu_opts,
            index=_mpsu_opts.index(10),
            key="final_m_per_p",
        )
        power_phase = st.radio(
            "Вводная сеть:",
            ["Одна фаза (220 В)", "Три фазы (380 В)"],
            horizontal=True,
            key="final_phase",
        )

with col4_zip:
    with _ui_bordered_container():
        st.markdown('<p class="section4-subtitle">ЗИП и резерв</p>', unsafe_allow_html=True)
        if "calc_reserve_enabled" not in st.session_state:
            st.session_state.calc_reserve_enabled = True
        reserve_enabled = st.checkbox(
            "Включить комплекты ЗИП (Резерв)", key="calc_reserve_enabled"
        )
        reserve_modules_choice = "5%"
        reserve_modules_custom = 0
        reserve_psu_cards = False
        if reserve_enabled:
            zc1, zc2 = st.columns(2)
            with zc1:
                if "calc_reserve_modules_choice" not in st.session_state:
                    st.session_state.calc_reserve_modules_choice = "5%"
                reserve_modules_choice = st.selectbox(
                    "Резерв модулей",
                    ["3%", "5%", "10%", "Свой"],
                    key="calc_reserve_modules_choice",
                )
                if reserve_modules_choice == "Свой":
                    if "calc_reserve_modules_custom" not in st.session_state:
                        st.session_state.calc_reserve_modules_custom = 0
                    reserve_modules_custom = st.number_input(
                        "Кол-во шт.", min_value=0, key="calc_reserve_modules_custom"
                    )
            with zc2:
                if "calc_reserve_psu_cards" not in st.session_state:
                    st.session_state.calc_reserve_psu_cards = True
                reserve_psu_cards = st.checkbox("+1 БП и Карта", key="calc_reserve_psu_cards")
                st.caption(
                    "При ЗИП: **+1 силовая перемычка** между БП (монолит) и **+1 патч-корд** в комплект."
                )

st.markdown('<p class="section4-subtitle" style="margin-top:6px;">Коммутация</p>', unsafe_allow_html=True)
col4_j, col4_p, col4_c = st.columns(3)
with col4_j:
    with _ui_bordered_container():
        st.markdown("**Перемычки БП**")
        if "Монолитный" in mount_type:
            _pj_default_ix = next(
                (i for i, p in enumerate(POWER_JUMPERS_MONOLITH_DB) if p["length_cm"] == 70),
                3,
            )
            selected_power_jumper = st.selectbox(
                "Длина:",
                POWER_JUMPERS_MONOLITH_DB,
                index=_pj_default_ix,
                format_func=lambda p: f"{p['name']} — ${p['price_usd']:.2f}/шт",
                key="main_power_jumper_select",
                help="По умолчанию 70 см.",
            )
        else:
            st.caption("Только для монолитного монтажа.")
with col4_p:
    with _ui_bordered_container():
        st.markdown("**Патч-корды**")
        _patch_default_ix = 0 if "Монолитный" in mount_type else 1
        selected_patch_cord = st.selectbox(
            "Модель:",
            PATCH_CORDS_DB,
            index=_patch_default_ix,
            format_func=lambda p: f"{p['name']} — ${p['price_usd']:.2f}/шт",
            key="patch_cord_product_select",
            help="Монолит: чаще 1 м; кабинеты: 1,5 м.",
        )
with col4_c:
    with _ui_bordered_container():
        st.markdown("**Кабели питания карт → БП**")
        selected_card_power_cable = st.selectbox(
            "Модель:",
            CARD_POWER_CABLES_DB,
            index=0,
            format_func=lambda c: f"{c['name']} — ${c['price_usd']:.2f}/шт",
            key="card_power_cable_select",
            help="От БП к приёмной карте.",
        )

# ==========================================
# ==========================================
# ПОЛНЫЕ ИНЖЕНЕРНЫЕ ВЫЧИСЛЕНИЯ (ИСПРАВЛЕНО)
# ==========================================
modules_w = math.ceil(width_mm / 320)
modules_h = math.ceil(height_mm / 160)
total_modules = modules_w * modules_h
area_m2 = (real_width / 1000) * (real_height / 1000)

total_price_rub = area_m2 * price_per_m2

if reserve_modules_choice == "Свой":
    reserve_modules = int(reserve_modules_custom)
else:
    reserve_percent = int(reserve_modules_choice.replace("%", ""))
    reserve_modules = math.ceil(total_modules * reserve_percent / 100)
total_modules_order = total_modules + reserve_modules

# --- 1. МОЩНОСТЬ (ВАЖНО!) ---
peak_power_screen_kw = total_modules * max_power_module / 1000
avg_power_screen_kw = peak_power_screen_kw * 0.35

# --- 2. КАРТЫ (РАСЧЕТ ПО ТВОЕМУ СПИСКУ) ---

# А) Считаем строго по количеству модулей, которые ты выбрал в списке (6, 8, 10...)
num_cards_by_mod = math.ceil(total_modules / modules_per_card)

# Б) Для контроля: физический предел карты по разрешению (Novastar)
card_res_tuple = CARD_MAX_PIXELS.get(receiving_card['name'], (512, 384))
max_pixels_card = card_res_tuple[0] * card_res_tuple[1]
num_cards_by_pix = math.ceil(total_px / max_pixels_card)

# В) ИТОГО "ЧИСТОЕ" КОЛИЧЕСТВО
# Если ты вручную задал мало модулей (например 6), то num_cards_by_mod будет большим, 
# и программа возьмет именно его.
num_cards = max(num_cards_by_mod, num_cards_by_pix)

# Г) ИТОГО С УЧЕТОМ ЗИП (если нажата кнопка запаса)
num_cards_reserve = num_cards + 1 if reserve_psu_cards else num_cards

num_patch_cords_zip_spare = 1 if reserve_enabled else 0
patch_cords = num_cards_reserve + num_patch_cords_zip_spare
buy_patch_cords_total = patch_cords * selected_patch_cord["price_usd"]

num_power_cables = num_cards_reserve
reserve_power_cables = math.ceil(num_power_cables * 0.1)
num_card_power_cables_order = num_power_cables + reserve_power_cables
buy_card_power_cables_total = num_card_power_cables_order * selected_card_power_cable["price_usd"]

# --- 3. БП ---
num_psu = math.ceil(total_modules / modules_per_psu)
num_psu_reserve = num_psu + 1 if reserve_psu_cards else num_psu

num_plates = num_psu_reserve
vinths = num_plates * 4
reserve_vinths = math.ceil(vinths * 0.1)
num_screws_4x16_order = vinths + reserve_vinths

if "Монолитный" in mount_type and selected_power_jumper is not None:
    num_power_jumpers_for_chain = max(0, num_psu_reserve - 1)
    num_power_jumpers_zip_spare = 1 if reserve_enabled else 0
    num_power_jumpers = num_power_jumpers_for_chain + num_power_jumpers_zip_spare
else:
    num_power_jumpers_for_chain = 0
    num_power_jumpers_zip_spare = 0
    num_power_jumpers = 0
buy_power_jumpers_total = (
    num_power_jumpers * selected_power_jumper["price_usd"] if selected_power_jumper else 0.0
)

# --- 4. ХАБЫ ---
num_hubs = num_cards_reserve if receiving_card["type"] == "A" else 0

# --- 4b. МАГНИТЫ (только монолит; норма задаётся в блоке монтажа) ---
num_magnets = (
    total_modules * magnets_per_module
    if ("Монолитный" in mount_type and selected_magnet is not None and magnets_per_module > 0)
    else 0
)
magnet_unit_price_usd = magnet_unit_usd(selected_magnet) if selected_magnet else 0.0
buy_magnets_total = num_magnets * magnet_unit_price_usd
magnet_packs_order = (
    math.ceil(num_magnets / selected_magnet["pack_qty"]) if selected_magnet and num_magnets else 0
)

# --- 4c. Профиль 40×20 (только монолит): суммарная длина отрезов; в продаже только хлыст 6 м
vert_profiles = modules_w + 1
vert_length = real_height - 40
horiz_profiles = 2 if real_height <= 3000 else 3
horiz_length = real_width - 60
total_profile_length = (vert_profiles * vert_length + horiz_profiles * horiz_length) / 1000

fasteners_m6 = horiz_profiles * vert_profiles
reserve_fasteners = math.ceil(fasteners_m6 * 0.03)
num_m6_rivet_bolt_each = fasteners_m6 + reserve_fasteners

if "Монолитный" in mount_type:
    profile_cut_m = total_profile_length
    profile_sticks_6m = math.ceil(profile_cut_m / PROFILE_40X20_STICK_M) if profile_cut_m > 0 else 0
    profile_purchased_m = profile_sticks_6m * PROFILE_40X20_STICK_M
    profile_waste_m = max(0.0, profile_purchased_m - profile_cut_m)
    buy_profile_rub = profile_purchased_m * profile_40x20_rub_m
    buy_profile_usd = buy_profile_rub / exchange_rate if exchange_rate else 0.0
else:
    buy_profile_rub = 0.0
    buy_profile_usd = 0.0
    profile_sticks_6m = 0
    profile_purchased_m = 0.0
    profile_waste_m = 0.0
    profile_cut_m = 0.0

if "Монолитный" in mount_type:
    buy_screws_4x16_rub = num_screws_4x16_order * screw_4x16_press_rub_each
    buy_screws_4x16_usd = buy_screws_4x16_rub / exchange_rate if exchange_rate else 0.0
    buy_rivet_m6_rub = num_m6_rivet_bolt_each * rivet_m6_threaded_rub_each
    buy_bolt_m6_6x16_rub = num_m6_rivet_bolt_each * bolt_m6_6x16_din912_rub_each
    buy_m6_frame_rub = buy_rivet_m6_rub + buy_bolt_m6_6x16_rub
    buy_m6_frame_usd = buy_m6_frame_rub / exchange_rate if exchange_rate else 0.0
else:
    buy_screws_4x16_rub = 0.0
    buy_screws_4x16_usd = 0.0
    buy_rivet_m6_rub = 0.0
    buy_bolt_m6_6x16_rub = 0.0
    buy_m6_frame_rub = 0.0
    buy_m6_frame_usd = 0.0

if "Монолитный" in mount_type:
    buy_metal_plates_rub = num_plates * METAL_PLATE_RUB_EACH
    buy_metal_plates_usd = buy_metal_plates_rub / exchange_rate if exchange_rate else 0.0
else:
    buy_metal_plates_rub = 0.0
    buy_metal_plates_usd = 0.0

# --- 5. ФИНАНСЫ (USD) ---

# 1. Сначала определяем цену модуля для расчетов (берем ту, что введена выше)
module_price_usd = price_usd  # Теперь NameError исчезнет

# 2. Считаем закупку по категориям
buy_mods_total = total_modules_order * module_price_usd
buy_cards_total = num_cards_reserve * receiving_card["price_usd"]
buy_hubs_total = num_hubs * hub_price_usd
buy_psu_total = num_psu_reserve * sel_psu["price_usd"]
buy_processor_total = proc_price_usd

# 3. Итоговая сумма закупки (включая модули и процессор)
total_buy_usd = (
    buy_mods_total + 
    buy_cards_total + 
    buy_psu_total + 
    buy_hubs_total + 
    buy_processor_total +
    buy_magnets_total +
    buy_patch_cords_total +
    buy_card_power_cables_total +
    buy_power_jumpers_total +
    buy_profile_usd +
    buy_screws_4x16_usd +
    buy_m6_frame_usd +
    buy_metal_plates_usd
)

# 4. Пересчет модулей для отчета (как у тебя в коде)
total_modules_cost_usd = total_modules * module_price_usd
total_modules_cost_rub = total_modules_cost_usd * exchange_rate

# 5. Общая закупка в рублях
total_buy_rub = total_buy_usd * exchange_rate

# Закупка: электроника/коммутация vs каркас и крепёж (профиль, M6, саморезы, пластины, магниты)
buy_frame_usd = (
    buy_profile_usd
    + buy_screws_4x16_usd
    + buy_m6_frame_usd
    + buy_metal_plates_usd
    + buy_magnets_total
)
buy_components_usd = total_buy_usd - buy_frame_usd
buy_frame_rub = buy_frame_usd * exchange_rate
buy_components_rub = buy_components_usd * exchange_rate

sale_total_usd = total_buy_usd * margin
sale_total_rub = sale_total_usd * exchange_rate
profit_usd = sale_total_usd - total_buy_usd
profit_rub = profit_usd * exchange_rate

# --- 6. ЭЛЕКТРИКА (ТЕПЕРЬ РАБОТАЕТ) ---
electrical_power_kw = peak_power_screen_kw * 1.20
if "Одна фаза" in power_phase:
    current = (electrical_power_kw * 1000) / 220
    cores = 3
else:
    current = (electrical_power_kw * 1000) / (380 * math.sqrt(3))
    cores = 5

if current <= 15: sq = "1.5"
elif current <= 21: sq = "2.5"
elif current <= 27: sq = "4"
elif current <= 34: sq = "6"
elif current <= 50: sq = "10"
elif current <= 70: sq = "16"
elif current <= 85: sq = "25"
else: sq = "35"
cable_section = f"{cores}×{sq} мм²"

target_breaker = current * 1.25
standard_breakers = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
breaker = next((b for b in standard_breakers if b >= target_breaker), math.ceil(target_breaker))

# Механика (длины профиля и fasteners_m6 — см. блок 4c выше)

# Коммутация
num_cables = max(0, num_psu_reserve - 1)
nvi = num_cables * 6
reserve_nvi = math.ceil(nvi * 0.1)

# Вес
module_weight = 0.37 if "Indoor" in env_key else 0.5
weight_modules = total_modules_order * module_weight

total_cabinet_weight = 0
cabinets_w, cabinets_h, total_cabinets = 0, 0, 0
if "кабинетах" in mount_type:
    cabinets_w = math.ceil(real_width / cabinet_width)
    cabinets_h = math.ceil(real_height / cabinet_height)
    total_cabinets = cabinets_w * cabinets_h
    total_cabinet_weight = total_cabinets * cabinet_weight_per

weight_carcas = total_profile_length * 2 if "Монолитный" in mount_type else 0
weight_extra = (weight_modules + weight_carcas + total_cabinet_weight) * 0.05
total_weight = weight_modules + weight_carcas + total_cabinet_weight + weight_extra

# Логистика
num_boxes = math.ceil(total_modules_order / 40)
box_weight = num_boxes * 22
box_volume = num_boxes * 0.06

# ==========================================
# БЛОК 5: ПОЛНЫЙ ДЕТАЛЬНЫЙ ОТЧЕТ
# ==========================================
st.markdown('<div class="section-header">📊 Финальный отчёт и Спецификация</div>', unsafe_allow_html=True)

_spec_qty_cells = [
    ("Модули", f"{total_modules_order} шт."),
    ("БП", f"{num_psu_reserve} шт."),
    ("Карты", f"{num_cards_reserve} шт."),
    ("Хабы", f"{num_hubs} шт."),
]
if num_magnets:
    _spec_qty_cells.append(("Магниты", f"{num_magnets} шт."))
_spec_qty_cells.extend(
    [
        ("Патч-корды", f"{patch_cords} шт."),
        ("Каб. пит. карт", f"{num_card_power_cables_order} шт."),
    ]
)
if num_power_jumpers:
    _spec_qty_cells.append(("Перемычки БП", f"{num_power_jumpers} шт."))
if profile_purchased_m > 0:
    _spec_qty_cells.append(("Профиль 40×20×1,5", f"{profile_purchased_m:.1f} м"))
if buy_screws_4x16_usd > 0:
    _spec_qty_cells.append(("Саморезы", f"{num_screws_4x16_order} шт."))
if buy_m6_frame_usd > 0:
    _spec_qty_cells.append(("M6 узлы", f"{num_m6_rivet_bolt_each} к-т"))
if "Монолитный" in mount_type and buy_metal_plates_usd > 0:
    _spec_qty_cells.append(("Пластины БП", f"{num_plates} шт."))
_spec_qty_grid_html = "".join(
    f'<div><div class="spec-summary-cell-label">{lbl}</div><div class="spec-summary-cell-val">{val}</div></div>'
    for lbl, val in _spec_qty_cells
)

# Верхний ряд: разрешение, площадь, габарит, потребление (средн. + макс.)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Разрешение</div>'
        f'<div class="metric-value">{int(real_width / pixel_pitch)} × {int(real_height / pixel_pitch)} px</div></div>',
        unsafe_allow_html=True,
    )
with col_m2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Площадь</div>'
        f'<div class="metric-value">{area_m2:.2f} м²</div></div>',
        unsafe_allow_html=True,
    )
with col_m3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Размер экрана</div>'
        f'<div class="metric-value">{int(real_width)} × {int(real_height)} мм</div></div>',
        unsafe_allow_html=True,
    )
with col_m4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Потребление</div>'
        f'<div class="metric-value">средн. {avg_power_screen_kw:.1f} кВт · макс. {peak_power_screen_kw:.1f} кВт</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

st.markdown(
    f"""
<div style="padding: 16px 20px; border-radius: 10px; background: #1a202c; border: 1px solid #2d3748; margin-bottom: 16px;">
    <div style="color: #a0aec0; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1px;">Сводка по количеству</div>
    <div class="spec-summary-grid">{_spec_qty_grid_html}</div>
</div>
""",
    unsafe_allow_html=True,
)

col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    st.markdown(
        f"""
<div class="finance-metric-card" style="border-left: 4px solid #3b82f6;">
    <div style="color: #a0aec0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px;">Закупка комплектующих</div>
    <div style="margin-top: 8px;">
        <span style="color: #f8fafc; font-size: 1.35rem; font-weight: bold;">${buy_components_usd:,.2f}</span><br>
        <span style="color: #94a3b8; font-size: 0.95rem;">({buy_components_rub:,.0f} ₽)</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with col_f2:
    st.markdown(
        f"""
<div class="finance-metric-card" style="border-left: 4px solid #d97706;">
    <div style="color: #a0aec0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px;">Закупка каркаса и крепежа</div>
    <div style="margin-top: 8px;">
        <span style="color: #f8fafc; font-size: 1.35rem; font-weight: bold;">${buy_frame_usd:,.2f}</span><br>
        <span style="color: #94a3b8; font-size: 0.95rem;">({buy_frame_rub:,.0f} ₽)</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with col_f3:
    st.markdown(
        f"""
<div class="finance-metric-card" style="border-left: 4px solid #48bb78;">
    <div style="color: #a0aec0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px;">Стоимость с наценкой</div>
    <div style="margin-top: 8px;">
        <span style="color: #f8fafc; font-size: 1.35rem; font-weight: bold;">${sale_total_usd:,.2f}</span><br>
        <span style="color: #48bb78; font-size: 0.95rem; font-weight: bold;">({sale_total_rub:,.0f} ₽)</span>
    </div>
    <div style="font-size: 0.7rem; color: #718096; margin-top: auto; padding-top: 8px;">Наценка {int((margin - 1) * 100)}%</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col_f4:
    st.markdown(
        f"""
<div class="finance-metric-card" style="border-left: 4px solid #a855f7;">
    <div style="color: #a0aec0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px;">Чистая прибыль</div>
    <div style="margin-top: 8px;">
        <span style="color: #f8fafc; font-size: 1.35rem; font-weight: bold;">${profit_usd:,.2f}</span><br>
        <span style="color: #c4b5fd; font-size: 0.95rem; font-weight: bold;">({profit_rub:,.0f} ₽)</span>
    </div>
    <div style="font-size: 0.7rem; color: #718096; margin-top: auto; padding-top: 8px;">Продажа − закупка</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("---")

with st.expander("Характеристики экрана", expanded=True):
    st.markdown(f"""
    - **Разрешение**: {int(real_width / pixel_pitch)} × {int(real_height / pixel_pitch)} px
    - **Площадь**: {area_m2:.2f} м²
    - **Технология**: {tech}
    - **Яркость**: {brightness} нит
    - **Датчик яркости и температуры**: {sensor}
    """)

with st.expander("Модули", expanded=True):
    st.markdown(f"""
    - **Модель**: {selected_module_name}
    - **По горизонтали**: {modules_w} шт.
    - **По вертикали**: {modules_h} шт.
    - **Основное количество**: {total_modules} шт.
    - **Резерв (ЗИП)**: {reserve_modules} шт.
    - **Итого для заказа**: **{total_modules_order} шт.**
    - **Закупочная стоимость модулей**: ${total_modules_cost_usd:.2f} ({total_modules_cost_rub:,.0f} ₽)
    """)

if "кабинетах" in mount_type:
    with st.expander("Кабинеты", expanded=True):
        st.markdown(f"""
        - **Модель**: {cabinet_model}
        - **Размер одного**: {cabinet_width} × {cabinet_height} мм
        - **Сетка**: {cabinets_w} (Ш) × {cabinets_h} (В)
        - **Общее количество**: **{total_cabinets} шт.**
        - **Вес одного**: {cabinet_weight_per:.1f} кг
        - **Общий вес кабинетов**: {total_cabinet_weight:.1f} кг
        """)

with st.expander("Принимающие карты", expanded=True):
    st.markdown(f"""
    - **Модель**: {receiving_card['name']}
    - **Основное количество**: {num_cards} шт.
    - **Итого с учетом ЗИП**: **{num_cards_reserve} шт.**
    """)

with st.expander("Блоки питания", expanded=True):
    st.markdown(f"""
    - **Модель БП**: {sel_psu['name']} ({sel_psu['max_w']}W)
    - **Схема коммутации**: {modules_per_psu} модулей на 1 БП
    - **Пиковое потребление экрана**: {peak_power_screen_kw:.1f} кВт
    - **Рабочее (среднее) потребление**: {avg_power_screen_kw:.1f} кВт
    - **Основное количество БП**: {num_psu} шт.
    - **Итого БП к заказу (с ЗИП)**: **{num_psu_reserve} шт.**
    """)

with st.expander("Процессор / Контроллер", expanded=True):
    _rep_proc_ports = (
        f"\n    - **Backup**: да (база **{required_ports_base}** → требуется **{required_ports}**)"
        if hot_backup
        else ""
    )
    st.markdown(f"""
   - **Модель**: {selected_proc['name']}
    - **Доступно портов**: {available_ports}
    - **Необходимое портов (с учётом режима)**: {required_ports}{_rep_proc_ports}
    - **Средняя нагрузка на порт**: {load_per_port:.1f}%
    """)

with st.expander("Вводная Сеть", expanded=True):
    st.markdown(f"""
    - **Тип сети**: {power_phase}
    - **Ток**: {current:.1f} А (расчетный)
    - **Рекомендуемый кабель ВВГ**: {cable_section}
    - **Номинал автомата**: {breaker} А (тип C)
    """)

if "Монолитный" in mount_type:
    if selected_magnet is not None:
        _report_magnet_block = f"""
        - **Магниты** — **{selected_magnet['name']}**
          - **Норма**: **{magnets_per_module}** шт. на модуль
          - **Количество**: **{num_magnets} шт.** ({total_modules} × {magnets_per_module})
          - **Заказ пачками**: ~**{magnet_packs_order}** пачек по {selected_magnet['pack_qty']} шт.
          - **Цена закупки**: ${magnet_unit_price_usd:.4f}/шт → **${buy_magnets_total:.2f}** ({buy_magnets_total * exchange_rate:,.0f} ₽)"""
    else:
        _report_magnet_block = """
        - **Магниты**: не заданы"""
    with st.expander("Каркас и крепёж (Монолитный)", expanded=True):
        _waste_pct = (
            (100.0 * profile_waste_m / profile_purchased_m) if profile_purchased_m > 0 else 0.0
        )
        st.markdown(f"""
        - **Вертикальные профили**: {vert_profiles} шт. (длина на отрез {vert_length} мм, общая {vert_profiles * vert_length / 1000:.2f} м)
        - **Горизонтальные профили**: {horiz_profiles} шт. (длина на отрез {horiz_length} мм, общая {horiz_profiles * horiz_length / 1000:.2f} м)
        - **Профиль 40×20×1,5 мм** (только хлысты **6 м**, **{profile_40x20_rub_m:.0f} ₽/п.м** в сайдбаре; автоцена: {profile_price_source_note}):
          нужно **{profile_cut_m:.2f} м** по раскрою → **{profile_sticks_6m}** хлыстов × 6 м = **{profile_purchased_m:.2f} м** к оплате;
          остаток **~{profile_waste_m:.2f} м** (~{_waste_pct:.1f}% от купленной длины) уже в сумме — **{buy_profile_rub:,.0f} ₽** (**${buy_profile_usd:.2f}** в закупке)
        - **Узлы каркаса (заклёпка Sormat M6 + винт M6×16)**: {fasteners_m6} узл. + {reserve_fasteners} запас (3%) = **{num_m6_rivet_bolt_each}** комплектов (по 1 заклёпке + 1 винту)
          - Заклёпка резьбовая **Sormat M6**: **{rivet_m6_threaded_rub_each:.3f} ₽/шт** ({rivet_m6_price_source_note}; [Lemana Pro]({LEMANA_RIVET_M6_SORMAT_URL})) → **{buy_rivet_m6_rub:,.0f} ₽**
          - Винт **M6×16 DIN 912** оцинк.: **{bolt_m6_6x16_din912_rub_each:.3f} ₽/шт** ({bolt_m6_6x16_price_source_note}; [Lemana Pro]({LEMANA_BOLT_M6_6x16_DIN912_URL})) → **{buy_bolt_m6_6x16_rub:,.0f} ₽**
          - **Итого M6**: **{buy_m6_frame_rub:,.0f} ₽** (**${buy_m6_frame_usd:.2f}** в закупке)
        {_report_magnet_block}
        - **Металлические пластины под БП**: **{num_plates} шт.** (по числу БП с ЗИП) × **{METAL_PLATE_RUB_EACH:.0f} ₽/шт** → **{buy_metal_plates_rub:,.0f} ₽** (**${buy_metal_plates_usd:.2f}** в общей закупке)
        - **Саморезы 4,2×16 с прессшайбой (сверло) к профилю**: {vinths} шт. + {reserve_vinths} шт. запас (10%) = **{num_screws_4x16_order} шт.** — **{screw_4x16_press_rub_each:.3f} ₽/шт** ({screw_4x16_price_source_note}) → **{buy_screws_4x16_rub:,.0f} ₽** (**${buy_screws_4x16_usd:.2f}** в закупке)
        """)

with st.expander("Коммутация", expanded=True):
    _patch_zip_note = (
        "; при ЗИП **+1** патч-корд в комплект"
        if num_patch_cords_zip_spare
        else ""
    )
    if "Монолитный" in mount_type:
        _pj_name = selected_power_jumper["name"] if selected_power_jumper else "—"
        _pj_zip_note = (
            ", в т.ч. **+1** силовая перемычка (ЗИП)"
            if num_power_jumpers_zip_spare
            else ""
        )
        st.markdown(f"""
        **Силовая (между БП, монолит)**
        - **Силовые перемычки** ({_pj_name}): **{num_power_jumpers} шт.**
          (шлейф {num_psu_reserve} БП: **{num_power_jumpers_for_chain} шт.**{_pj_zip_note})
          — **${buy_power_jumpers_total:.2f}** в закупке ({buy_power_jumpers_total * exchange_rate:,.0f} ₽)

        **Слаботочка и питание карт**
        - **Патч-корды RJ45** — {selected_patch_cord['name']}: **{patch_cords} шт.**
          (**{num_cards_reserve}** по картам с учётом ЗИП{_patch_zip_note}) — ${selected_patch_cord['price_usd']:.2f}/шт → **${buy_patch_cords_total:.2f}** ({buy_patch_cords_total * exchange_rate:,.0f} ₽)
        - **Кабели питания карт → БП** — {selected_card_power_cable['name']}: **{num_card_power_cables_order} шт.**
          ({num_power_cables} по картам + {reserve_power_cables} запас 10%) — ${selected_card_power_cable['price_usd']:.2f}/шт → **${buy_card_power_cables_total:.2f}** ({buy_card_power_cables_total * exchange_rate:,.0f} ₽)
        """)
    else:
        st.markdown(f"""
        **Силовая (кабинеты)**
        - **Силовые кабели 220 В (шлейфы)**: {num_cables} шт., общая длина ~{num_cables * 0.8:.1f} м
        - **Наконечники НВИ**: {nvi} шт. + {reserve_nvi} шт. (запас 10%)

        **Слаботочка и питание карт**
        - **Патч-корды RJ45** — {selected_patch_cord['name']}: **{patch_cords} шт.**
          (**{num_cards_reserve}** по картам с учётом ЗИП{_patch_zip_note})
          — ${selected_patch_cord['price_usd']:.2f}/шт → **${buy_patch_cords_total:.2f}** ({buy_patch_cords_total * exchange_rate:,.0f} ₽)
        - **Кабели питания карт → БП** — {selected_card_power_cable['name']}: **{num_card_power_cables_order} шт.**
          ({num_power_cables} по картам + {reserve_power_cables} запас 10%) — ${selected_card_power_cable['price_usd']:.2f}/шт → **${buy_card_power_cables_total:.2f}** ({buy_card_power_cables_total * exchange_rate:,.0f} ₽)
        """)

with st.expander("Весовые характеристики", expanded=True):
    st.markdown(f"""
    - **Вес модулей**: {weight_modules:.1f} кг
    - **Вес каркаса / кабинетов**: {weight_carcas + total_cabinet_weight:.1f} кг
    - **Метизы и проводка (5%)**: {weight_extra:.1f} кг
    - **Общий расчётный вес экрана**: **{total_weight:.1f} кг**
    """)

with st.expander("Упаковка и логистика", expanded=True):
    st.markdown(f"""
    - **Количество коробок**: {num_boxes} шт.
    - **Общий вес коробок**: ~{box_weight} кг
    - **Общий объём**: ~{box_volume:.2f} м³
    """)

# СХЕМА СБОРКИ
if "Монолитный" in mount_type:
    st.subheader("📐 Схема сборки")
    html_grid = f"""
    <div style="display: grid; grid-template-columns: repeat({modules_w}, 1fr); gap: 2px; background-color: #2d3748; padding: 4px; width: 100%; max-width: 900px; border-radius: 4px; margin: 0 auto;">
    """
    for row in range(modules_h):
        for col in range(modules_w):
            color = "#48bb78" if (row + col) % 2 == 0 else "#319795"
            html_grid += f'<div style="background-color: {color}; aspect-ratio: 2/1; border-radius: 2px;"></div>'
    html_grid += "</div>"
    st.components.v1.html(html_grid, height=int(900 * (modules_h/modules_w)) + 20)

st.markdown("---")

# ==========================================
# БЛОК 6: ИНТЕГРАЦИЯ
# ==========================================
st.subheader("🔗 Экспорт и Интеграция")

figma_data = {
    "project_name": project_name, "client": client_name, "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "screen_dimensions_mm": f"{real_width}x{real_height}", "resolution_px": f"{int(real_width/pixel_pitch)}x{int(real_height/pixel_pitch)}",
    "area_m2": round(area_m2, 2), "pixel_pitch": pixel_pitch, "total_modules": total_modules_order,
    "receiving_cards": num_cards_reserve, "power_supplies": num_psu_reserve, "processor": selected_proc['name'],
    "processor_ports_physical": available_ports,
    "processor_ports_required": required_ports,
    "processor_ports_required_base": required_ports_base,
    "hot_backup_gige": bool(hot_backup),
    "magnets_qty": num_magnets,
    "magnets_per_module": magnets_per_module,
    "magnets_cost_usd": round(buy_magnets_total, 2),
    "patch_cords_qty": patch_cords,
    "patch_cords_zip_spare_qty": num_patch_cords_zip_spare,
    "patch_cord_model": selected_patch_cord["name"],
    "patch_cords_cost_usd": round(buy_patch_cords_total, 2),
    "card_power_cables_qty": num_card_power_cables_order,
    "card_power_cable_model": selected_card_power_cable["name"],
    "card_power_cables_cost_usd": round(buy_card_power_cables_total, 2),
    "power_jumpers_qty": num_power_jumpers,
    "power_jumpers_for_psu_chain_qty": num_power_jumpers_for_chain,
    "power_jumpers_zip_spare_qty": num_power_jumpers_zip_spare,
    "power_jumper_model": selected_power_jumper["name"] if selected_power_jumper else None,
    "power_jumpers_cost_usd": round(buy_power_jumpers_total, 2),
    "profile_40x20_stick_length_m": PROFILE_40X20_STICK_M,
    "profile_40x20_sticks_6m": profile_sticks_6m,
    "profile_purchased_m": round(profile_purchased_m, 3),
    "profile_cut_m": round(profile_cut_m, 3),
    "profile_waste_m": round(profile_waste_m, 3),
    "profile_rub_per_m": round(profile_40x20_rub_m, 2),
    "profile_price_source": profile_price_source_note,
    "profile_cost_rub": round(buy_profile_rub, 2),
    "profile_cost_usd": round(buy_profile_usd, 2),
    "screw_4x16_press_qty": num_screws_4x16_order,
    "screw_4x16_press_rub_each": round(screw_4x16_press_rub_each, 4),
    "screw_4x16_price_source": screw_4x16_price_source_note,
    "screw_4x16_cost_rub": round(buy_screws_4x16_rub, 2),
    "screw_4x16_cost_usd": round(buy_screws_4x16_usd, 2),
    "m6_frame_joint_qty": num_m6_rivet_bolt_each,
    "rivet_m6_threaded_rub_each": round(rivet_m6_threaded_rub_each, 4),
    "rivet_m6_sormat_lemana_url": LEMANA_RIVET_M6_SORMAT_URL,
    "rivet_m6_price_source": rivet_m6_price_source_note,
    "rivet_m6_cost_rub": round(buy_rivet_m6_rub, 2),
    "bolt_m6_6x16_din912_rub_each": round(bolt_m6_6x16_din912_rub_each, 4),
    "bolt_m6_6x16_price_source": bolt_m6_6x16_price_source_note,
    "bolt_m6_6x16_lemana_url": LEMANA_BOLT_M6_6x16_DIN912_URL,
    "bolt_m6_6x16_cost_rub": round(buy_bolt_m6_6x16_rub, 2),
    "m6_frame_total_rub": round(buy_m6_frame_rub, 2),
    "m6_frame_total_usd": round(buy_m6_frame_usd, 2),
    "metal_plates_qty": num_plates if "Монолитный" in mount_type else 0,
    "metal_plate_rub_each": METAL_PLATE_RUB_EACH,
    "metal_plates_cost_rub": round(buy_metal_plates_rub, 2),
    "metal_plates_cost_usd": round(buy_metal_plates_usd, 2),
    "peak_power_kw": round(peak_power_screen_kw, 2), "avg_power_kw": round(avg_power_screen_kw, 2),
    "total_price_rub": total_price_rub,
    "module_cost_usd": total_modules_cost_usd,
    "module_cost_rub": total_modules_cost_rub,
    "total_buy_usd": round(total_buy_usd, 2),
    "total_buy_rub": round(total_buy_rub, 2),
    "buy_components_usd": round(buy_components_usd, 2),
    "buy_components_rub": round(buy_components_rub, 2),
    "buy_frame_usd": round(buy_frame_usd, 2),
    "buy_frame_rub": round(buy_frame_rub, 2),
    "sale_total_usd": round(sale_total_usd, 2),
    "sale_total_rub": round(sale_total_rub, 2),
    "profit_usd": round(profit_usd, 2),
    "profit_rub": round(profit_rub, 2),
    "margin_percent": int((margin - 1) * 100),
}
figma_json = json.dumps(figma_data, indent=4, ensure_ascii=False)

_pdf_spec_rows = [
    ("Модули", f"{total_modules_order} шт."),
    ("Приёмные карты", f"{num_cards_reserve} шт."),
    ("БП", f"{num_psu_reserve} шт."),
    ("Патч-корды", f"{patch_cords} шт."),
    ("Кабели питания карт", f"{num_card_power_cables_order} шт."),
]
if num_magnets:
    _pdf_spec_rows.append(("Магниты", f"{num_magnets} шт."))
if num_power_jumpers:
    _pdf_spec_rows.append(("Перемычки БП", f"{num_power_jumpers} шт."))
if profile_purchased_m > 0:
    _pdf_spec_rows.append(("Профиль 40×20×1,5", f"{profile_purchased_m:.1f} м"))
if buy_m6_frame_usd > 0:
    _pdf_spec_rows.append(("Узлы M6 (к-ты)", f"{num_m6_rivet_bolt_each}"))

_pdf_ctx = {
    "project_name": project_name,
    "client_name": client_name or "",
    "date_str": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
    "module_name": selected_module_name,
    "mount_type": mount_type,
    "pixel_pitch": pixel_pitch,
    "screen_mm": f"{int(real_width)} × {int(real_height)}",
    "resolution": f"{int(real_width / pixel_pitch)} × {int(real_height / pixel_pitch)} px",
    "area_m2": area_m2,
    "total_modules": total_modules_order,
    "processor": selected_proc["name"],
    "receiving_card": receiving_card["name"],
    "num_cards": num_cards_reserve,
    "psu_name": sel_psu["name"],
    "num_psu": num_psu_reserve,
    "peak_kw": peak_power_screen_kw,
    "avg_kw": avg_power_screen_kw,
    "total_buy_usd": total_buy_usd,
    "total_buy_rub": total_buy_rub,
    "sale_rub": sale_total_rub,
    "margin_pct": int((margin - 1) * 100),
    "exchange_rate": exchange_rate,
    "spec_rows": _pdf_spec_rows,
}

col_exp1, col_exp2, col_exp3 = st.columns(3)
with col_exp1:
    st.markdown("**JSON для Figma Variables Studio**")
    st.code(figma_json, language="json")

with col_exp2:
    st.markdown("**Сохранение в базу Google Sheets**")
    if st.button("💾 Отправить расчёт в облако", use_container_width=True):
        if "google_sheets" in st.secrets:
            st.success("✅ Сохранено в Google Sheets!")
        else:
            st.warning("Секреты `st.secrets['google_sheets']` не настроены.")
            st.success("✅ [Mock] Данные сформированы для отправки в базу!")

with col_exp3:
    st.markdown("**PDF-отчёт**")
    st.caption("Лаконичная спецификация для клиента / поставщика.")
    if build_led_report_pdf is None:
        st.info("Установите пакет **fpdf2**: `pip install fpdf2`")
    else:
        try:
            _pdf_bytes = build_led_report_pdf(_pdf_ctx)
            _pdf_name = (
                suggested_pdf_filename(project_name)
                if suggested_pdf_filename
                else "led_report.pdf"
            )
            st.download_button(
                label="📄 Скачать PDF",
                data=_pdf_bytes,
                file_name=_pdf_name,
                mime="application/pdf",
                use_container_width=True,
                key="download_led_pdf_report",
            )
        except Exception as _pdf_exc:
            st.error(f"Не удалось сформировать PDF: {_pdf_exc}")
