"""
Лаконичный PDF-отчёт по расчёту LED (кириллица через DejaVu из пакета fpdf2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List, Tuple


def _font_paths() -> Tuple[str | None, str | None]:
    try:
        import fpdf

        base = Path(fpdf.__file__).resolve().parent / "font"
        reg = base / "DejaVuSans.ttf"
        bold = base / "DejaVuSans-Bold.ttf"
        if reg.is_file():
            return str(reg), str(bold) if bold.is_file() else str(reg)
    except Exception:
        pass
    return None, None


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

    reg, bold = _font_paths()
    if not reg:
        raise RuntimeError("Не найден шрифт DejaVu в fpdf2 — переустановите пакет fpdf2")

    class PDF(FPDF):
        def footer(self) -> None:
            self.set_y(-12)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(130, 140, 150)
            self.cell(0, 8, "MediaLive · LED Calculator", align="C", ln=0)

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    pdf.add_font("DejaVu", "", reg)
    pdf.add_font("DejaVu", "B", bold or reg)

    # Шапка
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_xy(18, 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 8, "Расчёт LED-экрана", ln=1)
    pdf.set_font("DejaVu", "", 9)
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
        pdf.set_font("DejaVu", "B", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 7, title, ln=1)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 41, 59)

    def row_kv(label: str, value: str) -> None:
        pdf.set_font("DejaVu", "", 10)
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
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(100, 116, 139)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)
    pdf.cell(w * 0.48, 6, "Курс USD (закупка), ₽", align="L", ln=0)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(w * 0.52, 6, f"{float(ctx.get('exchange_rate', 0)):.2f}", align="R", ln=1)
    row_kv("Закупка всего, USD", f"${float(ctx.get('total_buy_usd', 0)):,.2f}".replace(",", " "))
    row_kv("Закупка всего, ₽", f"{float(ctx.get('total_buy_rub', 0)):,.0f} ₽".replace(",", " "))
    row_kv("Продажа (итого), ₽", f"{float(ctx.get('sale_rub', 0)):,.0f} ₽".replace(",", " "))
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(37, 99, 235)
    pdf.set_x(pdf.l_margin)
    pdf.cell(w * 0.48, 8, "Наценка на железо", align="L", ln=0)
    pdf.cell(w * 0.52, 8, f"{int(ctx.get('margin_pct', 0))} %", align="R", ln=1)

    spec: List[Tuple[str, str]] = ctx.get("spec_rows") or []
    if spec:
        section("Спецификация (количества)")
        pdf.set_font("DejaVu", "", 9)
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


def suggested_pdf_filename(project_name: str) -> str:
    return _safe_filename(project_name)
