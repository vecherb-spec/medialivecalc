"""
Лаконичный PDF-отчёт по расчёту LED (Unicode TTF).
Шрифт: DejaVu рядом с модулем / в пакете fpdf2 / системный Arial или DejaVu (Linux).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, List, Tuple

FONT_FAMILY = "MLReport"  # произвольное имя семейства для add_font


def _bold_candidate(regular: Path) -> Path | None:
    d = regular.parent
    n = regular.name
    pairs = {
        "DejaVuSans.ttf": "DejaVuSans-Bold.ttf",
        "arial.ttf": "arialbd.ttf",
        "CALIBRI.TTF": "CALIBRIB.TTF",
        "calibri.ttf": "calibrib.ttf",
        "LiberationSans-Regular.ttf": "LiberationSans-Bold.ttf",
    }
    key = n
    if key in pairs:
        p = d / pairs[key]
        return p if p.is_file() else None
    low = n.lower()
    for k, v in pairs.items():
        if k.lower() == low:
            p = d / v
            return p if p.is_file() else None
    return None


def _font_candidates() -> list[Path]:
    """Пути по убыванию предпочтения."""
    out: list[Path] = []
    here = Path(__file__).resolve().parent
    out.extend(
        [
            here / "fonts" / "DejaVuSans.ttf",
            here / "DejaVu-sans" / "DejaVuSans.ttf",
        ]
    )
    try:
        import fpdf

        pkg_font = Path(fpdf.__file__).resolve().parent / "font" / "DejaVuSans.ttf"
        out.append(pkg_font)
    except Exception:
        pass
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        fdir = windir / "Fonts"
        out.extend(
            [
                fdir / "arial.ttf",
                fdir / "calibri.ttf",
            ]
        )
    else:
        out.extend(
            [
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/local/share/fonts/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            ]
        )
    return out


def _resolve_font_paths() -> Tuple[str, str]:
    """Возвращает (regular, bold) — bold может совпадать с regular."""
    for cand in _font_candidates():
        if cand.is_file():
            bd = _bold_candidate(cand)
            reg = str(cand.resolve())
            bol = str(bd.resolve()) if bd and bd.is_file() else reg
            return reg, bol
    return "", ""


def _safe_filename(name: str) -> str:
    s = re.sub(r'[^\w\-]+', "_", (name or "project").strip(), flags=re.UNICODE)
    return (s[:60] or "project") + ".pdf"


def build_led_report_pdf(ctx: dict[str, Any]) -> bytes:
    """
    ctx ожидает ключи: project_name, client_name, date_str, module_name, mount_type,
    pixel_pitch, screen_mm, resolution, area_m2, total_modules, processor,
    receiving_card, num_cards, psu_name, num_psu, peak_kw, avg_kw,
    total_buy_usd, total_buy_rub, sale_rub, margin_pct, exchange_rate,
    spec_rows (опц.) — список (подпись, значение) для компактной таблицы.
    """
    from fpdf import FPDF

    reg, bold = _resolve_font_paths()
    if not reg:
        raise RuntimeError(
            "Не найден TTF с кириллицей. Варианты: положите DejaVuSans.ttf в папку "
            "`fonts/` рядом с pdf_report.py (скачать с dejavu-fonts.github.io), "
            "или используйте Windows/Linux со шрифтами Arial / DejaVu в системе."
        )

    class PDF(FPDF):
        def footer(self) -> None:
            self.set_y(-12)
            self.set_font(FONT_FAMILY, "", 8)
            self.set_text_color(130, 140, 150)
            self.cell(0, 8, "MediaLive · LED Calculator", align="C", ln=0)

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    pdf.add_font(FONT_FAMILY, "", reg)
    pdf.add_font(FONT_FAMILY, "B", bold)

    # Шапка
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_xy(18, 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FONT_FAMILY, "B", 16)
    pdf.cell(0, 8, "Расчёт LED-экрана", ln=1)
    pdf.set_font(FONT_FAMILY, "", 9)
    pdf.set_x(18)
    sub = ctx.get("project_name") or "—"
    if ctx.get("client_name"):
        sub += f"  ·  {ctx['client_name']}"
    pdf.cell(0, 5, sub, ln=1)
    pdf.set_x(18)
    pdf.cell(0, 5, ctx.get("date_str") or "", ln=1)

    pdf.set_y(48)
    pdf.set_text_color(30, 41, 59)

    def section(title: str) -> None:
        pdf.ln(4)
        pdf.set_font(FONT_FAMILY, "B", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 7, title, ln=1)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 41, 59)

    def row_kv(label: str, value: str) -> None:
        pdf.set_font(FONT_FAMILY, "", 10)
        w = pdf.w - pdf.l_margin - pdf.r_margin
        w_l = w * 0.48
        w_r = w * 0.52
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(w_l, 6, label, align="L", ln=0)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(w_r, 6, str(value), align="R", ln=1)

    section("Экран и модуль")
    row_kv("Модуль (прайс)", str(ctx.get("module_name", "—")))
    row_kv("Монтаж", str(ctx.get("mount_type", "—")))
    row_kv("Шаг пикселя", f"P{ctx.get('pixel_pitch', '—')}")
    row_kv("Габарит экрана, мм", str(ctx.get("screen_mm", "—")))
    row_kv("Разрешение", str(ctx.get("resolution", "—")))
    row_kv("Площадь, м²", f"{float(ctx.get('area_m2', 0)):.2f}")
    row_kv("Модулей к заказу", str(ctx.get("total_modules", "—")))

    section("Управление и питание")
    row_kv("Процессор", str(ctx.get("processor", "—")))
    row_kv("Приёмная карта", str(ctx.get("receiving_card", "—")))
    row_kv("Приёмные карты, шт.", str(ctx.get("num_cards", "—")))
    row_kv("БП", str(ctx.get("psu_name", "—")))
    row_kv("БП к заказу, шт.", str(ctx.get("num_psu", "—")))
    row_kv("Пик / средняя мощность, кВт", f"{float(ctx.get('peak_kw', 0)):.2f} / {float(ctx.get('avg_kw', 0)):.2f}")

    section("Финансы (закупка и продажа)")
    pdf.set_font(FONT_FAMILY, "", 10)
    pdf.set_text_color(100, 116, 139)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)
    pdf.cell(w * 0.48, 6, "Курс USD (закупка), ₽", align="L", ln=0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(w * 0.52, 6, f"{float(ctx.get('exchange_rate', 0)):.2f}", align="R", ln=1)
    row_kv("Закупка всего, USD", f"${float(ctx.get('total_buy_usd', 0)):,.2f}".replace(",", " "))
    row_kv("Закупка всего, ₽", f"{float(ctx.get('total_buy_rub', 0)):,.0f} ₽".replace(",", " "))
    row_kv("Продажа (итого), ₽", f"{float(ctx.get('sale_rub', 0)):,.0f} ₽".replace(",", " "))
    pdf.set_font(FONT_FAMILY, "B", 10)
    pdf.set_text_color(37, 99, 235)
    pdf.set_x(pdf.l_margin)
    pdf.cell(w * 0.48, 8, "Наценка на железо", align="L", ln=0)
    pdf.cell(w * 0.52, 8, f"{int(ctx.get('margin_pct', 0))} %", align="R", ln=1)

    spec: List[Tuple[str, str]] = ctx.get("spec_rows") or []
    if spec:
        section("Спецификация (количества)")
        pdf.set_font(FONT_FAMILY, "", 9)
        fill = False
        for lab, val in spec[:18]:
            if fill:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_x(pdf.l_margin)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(w * 0.62, 5.5, str(lab)[:72], fill=True, align="L", ln=0)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(w * 0.38, 5.5, str(val)[:40], fill=True, align="R", ln=1)
            fill = not fill

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)


def build_led_kp_mvp_pdf(ctx: dict[str, Any]) -> bytes:
    """
    MVP-версия коммерческого предложения в более "презентационном" стиле.
    Ожидаемые ключи:
    - offer_no, date_str, project_name, client_name
    - screen_mm, resolution, module_name, mount_type
    - area_m2, total_modules, processor
    - cost_rows: list[tuple(name, qty, unit_rub, total_rub)]
    - subtotal_rub, vat_pct, vat_amount_rub, total_rub
    - note_terms, note_lead_time, note_warranty
    """
    from fpdf import FPDF

    reg, bold = _resolve_font_paths()
    if not reg:
        raise RuntimeError(
            "Не найден TTF с кириллицей. Добавьте DejaVuSans.ttf рядом с pdf_report.py."
        )

    class PDF(FPDF):
        def footer(self) -> None:
            self.set_y(-11)
            self.set_font(FONT_FAMILY, "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, f"MediaLive · стр. {self.page_no()}", align="C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()
    pdf.add_font(FONT_FAMILY, "", reg)
    pdf.add_font(FONT_FAMILY, "B", bold)

    # Header
    pdf.set_fill_color(17, 24, 39)
    pdf.rect(0, 0, 210, 44, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(14, 10)
    pdf.set_font(FONT_FAMILY, "B", 16)
    pdf.cell(0, 8, "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ", ln=1)
    pdf.set_font(FONT_FAMILY, "", 10)
    pdf.set_x(14)
    offer_no = str(ctx.get("offer_no", "—"))
    pdf.cell(0, 6, f"№ {offer_no} от {ctx.get('date_str', '')}", ln=1)
    pdf.set_x(14)
    pdf.cell(0, 6, "MediaLive · Продажа и аренда LED-экранов", ln=1)

    pdf.set_y(50)
    pdf.set_text_color(20, 20, 20)

    def section(title: str) -> None:
        pdf.ln(2)
        pdf.set_font(FONT_FAMILY, "B", 11)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(0, 7, title, ln=1)
        pdf.set_draw_color(229, 231, 235)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(2)
        pdf.set_text_color(20, 20, 20)

    def row(label: str, value: str) -> None:
        w = pdf.w - pdf.l_margin - pdf.r_margin
        wl = w * 0.38
        wr = w * 0.62
        pdf.set_font(FONT_FAMILY, "", 9.5)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(wl, 6, label, ln=0)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(wr, 6, value, align="R", ln=1)

    section("Проект")
    row("Проект", str(ctx.get("project_name", "—")))
    row("Клиент", str(ctx.get("client_name", "—")))
    row("Экран, мм", str(ctx.get("screen_mm", "—")))
    row("Разрешение", str(ctx.get("resolution", "—")))
    row("Модель модуля", str(ctx.get("module_name", "—")))
    row("Монтаж", str(ctx.get("mount_type", "—")))
    row("Площадь", f"{float(ctx.get('area_m2', 0)):.2f} м²")
    row("Количество модулей", str(ctx.get("total_modules", "—")))
    row("Процессор", str(ctx.get("processor", "—")))

    section("Стоимость проекта")
    rows: List[Tuple[str, str, float, float]] = ctx.get("cost_rows") or []
    # Header row
    w = pdf.w - pdf.l_margin - pdf.r_margin
    c1, c2, c3, c4 = w * 0.46, w * 0.14, w * 0.18, w * 0.22
    pdf.set_fill_color(243, 244, 246)
    pdf.set_text_color(55, 65, 81)
    pdf.set_font(FONT_FAMILY, "B", 9)
    pdf.cell(c1, 7, "Наименование", border=0, ln=0, fill=True)
    pdf.cell(c2, 7, "Кол-во", border=0, ln=0, align="C", fill=True)
    pdf.cell(c3, 7, "Цена, ₽", border=0, ln=0, align="R", fill=True)
    pdf.cell(c4, 7, "Сумма, ₽", border=0, ln=1, align="R", fill=True)

    pdf.set_font(FONT_FAMILY, "", 9)
    alt = False
    for name, qty, unit_rub, total_rub in rows:
        pdf.set_fill_color(255, 255, 255) if not alt else pdf.set_fill_color(249, 250, 251)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(c1, 6.5, str(name)[:48], ln=0, fill=True)
        pdf.cell(c2, 6.5, str(qty), ln=0, align="C", fill=True)
        pdf.cell(c3, 6.5, f"{float(unit_rub):,.0f}".replace(",", " "), ln=0, align="R", fill=True)
        pdf.cell(c4, 6.5, f"{float(total_rub):,.0f}".replace(",", " "), ln=1, align="R", fill=True)
        alt = not alt

    subtotal = float(ctx.get("subtotal_rub", 0))
    vat_amount = float(ctx.get("vat_amount_rub", 0))
    total = float(ctx.get("total_rub", 0))
    vat_pct = int(ctx.get("vat_pct", 22))

    pdf.ln(2)
    pdf.set_font(FONT_FAMILY, "B", 10)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(c1 + c2 + c3, 7, "ИТОГО (без НДС):", ln=0, align="R")
    pdf.set_text_color(17, 24, 39)
    pdf.cell(c4, 7, f"{subtotal:,.0f} ₽".replace(",", " "), ln=1, align="R")

    pdf.set_font(FONT_FAMILY, "", 9.5)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(c1 + c2 + c3, 6, f"НДС {vat_pct}%:", ln=0, align="R")
    pdf.cell(c4, 6, f"{vat_amount:,.0f} ₽".replace(",", " "), ln=1, align="R")

    pdf.set_fill_color(34, 197, 94)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FONT_FAMILY, "B", 11)
    pdf.cell(c1 + c2 + c3, 8, "ИТОГОВАЯ СТОИМОСТЬ:", ln=0, align="R", fill=True)
    pdf.cell(c4, 8, f"{total:,.0f} ₽".replace(",", " "), ln=1, align="R", fill=True)

    section("Условия")
    pdf.set_font(FONT_FAMILY, "", 9.5)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 5.5, f"Оплата: {ctx.get('note_terms', '100% предоплата по счёту.')}")
    pdf.multi_cell(0, 5.5, f"Срок поставки: {ctx.get('note_lead_time', 'по договорённости.')}")
    pdf.multi_cell(0, 5.5, f"Гарантия: {ctx.get('note_warranty', '3 года.')}")

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    if isinstance(out, str):
        return out.encode("latin-1")
    return bytes(out)


def suggested_pdf_filename(project_name: str) -> str:
    return _safe_filename(project_name)


def suggested_kp_pdf_filename(project_name: str) -> str:
    base = _safe_filename(project_name).replace(".pdf", "")
    return f"{base}_kp.pdf"
