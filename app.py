#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import sys
from datetime import datetime
from textwrap import indent

# ===== PDF =====
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

# =========================
# ANSI COLORS
# =========================
class ANSI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    GRAY = "\033[90m"

def c(text, color): return f"{color}{text}{ANSI.RESET}"
def ok(text): return c(text, ANSI.GREEN)
def warn(text): return c(text, ANSI.YELLOW)
def err(text): return c(text, ANSI.RED)
def info(text): return c(text, ANSI.CYAN)
def title(text): return c(text, ANSI.BOLD + ANSI.MAGENTA)
def hr(): return c("=" * 80, ANSI.GRAY)

# =========================
# CONSTANTS
# =========================

MODULE_W_MM = 320
MODULE_H_MM = 160

SPECS = {
    "indoor": {"max_w":24,"avg_w":8,"weight":0.37,"max_a":5.2},
    "outdoor": {"max_w":40,"avg_w":13,"weight":0.42,"max_a":9.2}
}

INDOOR_PITCHES=[0.8,1.0,1.25,1.37,1.53,1.66,1.86,2.0,2.5,3.07,4.0]
OUTDOOR_PITCHES=[2.5,3.07,4.0,5.0,6.0,6.66,8.0,10.0]

RECEIVING_CARDS = {
    1:("A5s Plus",320,256),2:("A7s Plus",512,256),3:("A8s",512,384),
    4:("A10s Pro",512,512),5:("MRV412",512,512),6:("MRV416",512,384),
    7:("MRV432",512,512),8:("MRV532",512,512),9:("NV3210",512,384),
    10:("MRV208",256,256),11:("MRV470",512,384),12:("A4s Plus",256,256)
}

# =========================
# INPUT
# =========================
def ask_int(prompt, default=None):
    while True:
        try:
            s=input(prompt).strip()
            if not s and default is not None: return default
            return int(s)
        except: print(err("Неверный ввод"))

def ask_float(prompt, default=None):
    while True:
        try:
            s=input(prompt).replace(",",".").strip()
            if not s and default is not None: return default
            return float(s)
        except: print(err("Неверный ввод"))

def ask_yes_no(prompt, default="y"):
    while True:
        s=input(prompt).lower().strip()
        if not s: s=default
        if s in ("y","yes","д","да"): return True
        if s in ("n","no","н","нет"): return False
        print(err("Введите y/n"))

# =========================
# CLASS
# =========================

class LEDCalculator_Qiangli_320x160:

    def __init__(self):
        pass

    def run(self):
        while True:
            self.collect()
            self.calculate()
            self.print_report()
            self.save_txt()
            self.export_pdf()
            if not ask_yes_no("\nЕщё расчёт? (y/n): ","n"):
                print(info("Работа завершена"))
                break

    # =========================
    # INPUT
    # =========================
    def collect(self):
        print(hr())
        print(title("LED КАЛЬКУЛЯТОР QIANGLI 320×160 (NOVASTAR)"))
        print(hr())

        # 1
        self.w_mm=ask_int("Введите ширину экрана (мм): ")
        self.h_mm=ask_int("Введите высоту экрана (мм): ")

        self.mx=math.ceil(self.w_mm/MODULE_W_MM)
        self.my=math.ceil(self.h_mm/MODULE_H_MM)
        self.modules=self.mx*self.my

        print(info(f"Модули: {self.mx} × {self.my} = {self.modules} шт"))

        # 2
        print("Тип экрана: 1.Indoor  2.Outdoor")
        self.screen="indoor" if ask_int("Выбор: ",1)==1 else "outdoor"

        # 4
        pitches=INDOOR_PITCHES if self.screen=="indoor" else OUTDOOR_PITCHES
        print("Доступные шаги:",pitches)
        self.pitch=ask_float("Введите шаг (мм): ",pitches[0])

        # 6
        print("Частота: 1920 / 2880 / 3840 / 6000 / 7680")
        self.refresh=ask_int("Введите: ",3840)

        # 8
        print("Выбор принимающей карты:")
        for k,v in RECEIVING_CARDS.items():
            print(f"{k}. {v[0]} {v[1]}×{v[2]} px")
        self.card_id=ask_int("Выбор: ",4)
        self.card=RECEIVING_CARDS[self.card_id]

        # 11
        self.mods_per_card=ask_int("Модулей на карту (8/10/12/16): ",8)

        # 12
        self.mods_per_psu=ask_int("Модулей на БП (4/6/8/10): ",8)

        # 13
        print("Запас питания: 1=15% 2=30%")
        self.margin=0.15 if ask_int("Выбор: ",2)==1 else 0.30

        # 14
        self.psu_w=ask_int("Мощность БП (200/300/400): ",200)

        # 16
        self.reserve=ask_yes_no("Добавить резерв? (y/n): ","n")
        self.reserve_modules=math.ceil(self.modules*0.05) if self.reserve else 0

    # =========================
    # CALC
    # =========================
    def calculate(self):
        spec=SPECS[self.screen]
        self.total_max_w=self.modules*spec["max_w"]*(1+self.margin)
        self.total_avg_w=self.modules*spec["avg_w"]

        self.psu_cnt=max(
            math.ceil(self.total_max_w/self.psu_w),
            math.ceil(self.modules/self.mods_per_psu)
        )

        self.cards=max(
            math.ceil(self.modules/self.mods_per_card),
            math.ceil((self.mx*self.my*MODULE_W_MM*MODULE_H_MM)/(self.card[1]*self.card[2]))
        )

        self.area=(self.mx*MODULE_W_MM/1000)*(self.my*MODULE_H_MM/1000)
        self.weight=self.modules*spec["weight"]

    # =========================
    # REPORT
    # =========================
    def print_report(self):
        self.lines=[]
        self.lines.append(hr())
        self.lines.append(title("ОТЧЁТ"))
        self.lines.append(hr())
        self.lines.append(f"Размер: {self.mx*320} × {self.my*160} мм")
        self.lines.append(f"Модули: {self.modules} шт (+{self.reserve_modules} резерв)")
        self.lines.append(f"Площадь: {self.area:.2f} м²")
        self.lines.append(f"Шаг: P{self.pitch}")
        self.lines.append(f"Частота: {self.refresh} Hz")
        self.lines.append(f"Питание (пик): {self.total_max_w/1000:.2f} кВт")
        self.lines.append(f"БП: {self.psu_cnt} шт по {self.psu_w} Вт")
        self.lines.append(f"Карты Novastar: {self.cards} шт ({self.card[0]})")
        self.lines.append(f"Вес модулей: {self.weight:.1f} кг")
        self.lines.append(hr())

        print("\n".join(self.lines))

    # =========================
    # SAVE TXT
    # =========================
    def save_txt(self):
        name=f"LED_Raschet_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(name,"w",encoding="utf-8") as f:
            f.write("\n".join(self.lines))
        print(ok(f"TXT сохранён: {name}"))

    # =========================
    # PDF EXPORT
    # =========================
    def export_pdf(self):
        name=f"LED_Raschet_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc=SimpleDocTemplate(name,pagesize=A4,leftMargin=30,rightMargin=30,topMargin=40,bottomMargin=30)
        styles=getSampleStyleSheet()

        story=[]
        story.append(Paragraph("ПРОФЕССИОНАЛЬНЫЙ РАСЧЁТ LED ЭКРАНА QIANGLI 320×160",styles["Title"]))
        story.append(Spacer(1,20))

        table_data=[["Параметр","Значение"],
            ["Размер",f"{self.mx*320} × {self.my*160} мм"],
            ["Модули",f"{self.modules} шт"],
            ["Площадь",f"{self.area:.2f} м²"],
            ["Шаг",f"P{self.pitch}"],
            ["Частота",f"{self.refresh} Hz"],
            ["Мощность",f"{self.total_max_w/1000:.2f} кВт"],
            ["БП",f"{self.psu_cnt} шт × {self.psu_w} Вт"],
            ["Карты",f"{self.cards} шт {self.card[0]}"],
            ["Вес",f"{self.weight:.1f} кг"],
        ]

        table=Table(table_data,repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003366")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),1,colors.grey),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("BACKGROUND",(0,1),(-1,-1),colors.whitesmoke),
        ]))

        story.append(table)
        doc.build(story)

        print(ok(f"PDF сохранён: {name}"))

# =========================
# RUN
# =========================
if __name__=="__main__":
    LEDCalculator_Qiangli_320x160().run()
