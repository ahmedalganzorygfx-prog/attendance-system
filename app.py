import os
import csv
import datetime
import re
import html
from decimal import Decimal, InvalidOperation
import subprocess
import webbrowser
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

# مكتبات إخراج PDF والتعريب
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# ---------------------------------------------------------
# إعدادات الخطوط والترقيم التلقائي لـ ReportLab
# ---------------------------------------------------------
font_path = "C:/Windows/Fonts/arial.ttf"
font_bold_path = "C:/Windows/Fonts/arialbd.ttf"

try:
    if os.path.exists(font_path) and os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
        pdfmetrics.registerFont(TTFont('ArabicFont-Bold', font_bold_path))
    else:
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path if os.path.exists(font_path) else 'Helvetica'))
        pdfmetrics.registerFont(TTFont('ArabicFont-Bold', font_bold_path if os.path.exists(font_bold_path) else 'Helvetica-Bold'))
except Exception:
    pass

def fix_arabic(text):
    if pd.isna(text) or text is None:
        return ""
    text_str = str(text).strip()
    reshaped_text = arabic_reshaper.reshape(text_str)
    return get_display(reshaped_text)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        try:
            self.setFont("ArabicFont", 9)
        except Exception:
            self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        self.line(36, 35, 806, 35)
        
        page_str = fix_arabic(f"صفحة {self._pageNumber} من {page_count}")
        footer_right = fix_arabic("الأكاديمية المهنية للمعلمين - فرع الجيزة | كشف حضور اليوم")
        
        self.drawString(36, 20, page_str)
        self.drawRightString(806, 20, footer_right)


def to_english_digits(value):
    if value is None:
        return ""
    s = str(value).strip()
    trans = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
        "01234567890123456789"
    )
    return s.translate(trans)

def normalize_national_id(value):
    s = to_english_digits(value).replace(" ", "").strip()
    if not s:
        return ""

    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?[Ee][+-]?\d+", s):
        try:
            s = format(Decimal(s), "f").split(".")[0]
        except (InvalidOperation, ValueError):
            pass

    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".", 1)[0]

    return s

class PATGizaQueueSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("الأكاديمية المهنية للمعلمين - فرع الجيزة | نظام أسبقية الحضور")
        self.root.geometry("680x780")
        self.root.resizable(False, False)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_file = os.path.join(base_dir, "teachers_database.csv")
        
        self.today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.daily_log_file = os.path.join(base_dir, f"حضور_{self.today_str}.csv")
        
        self.current_number = 1
        self.database = {}
        self.selected_teacher = None

        self.load_database()
        self.init_daily_log_csv()
        self.setup_ui()

    def load_database(self):
        if not os.path.exists(self.db_file):
            messagebox.showerror("خطأ", f"لم يتم العثور على ملف البيانات ({self.db_file}) في مجلد البرنامج!")
            return

        encodings_to_try = ['utf-8-sig', 'cp1256', 'windows-1256', 'utf-8']
        file_read_success = False

        for enc in encodings_to_try:
            try:
                with open(self.db_file, mode='r', encoding=enc, newline='') as file:
                    sample = file.read(4096)
                    file.seek(0)
                    delimiter = ';' if sample.count(';') > sample.count(',') else ','

                    reader = csv.DictReader(file, delimiter=delimiter)

                    for row in reader:
                        clean_row = {
                            str(k).strip(): str(v).strip()
                            for k, v in row.items()
                            if k is not None and v is not None
                        }

                        code = (
                            clean_row.get("Teacher_Code")
                            or clean_row.get("Code")
                            or clean_row.get("كود المعلم")
                            or clean_row.get("الكود")
                            or ""
                        )
                        national_id = (
                            clean_row.get("National_ID")
                            or clean_row.get("الرقم القومي")
                            or clean_row.get("رقم القومي")
                            or ""
                        )
                        name = (
                            clean_row.get("Name")
                            or clean_row.get("الاسم")
                            or clean_row.get("اسم المعلم")
                            or ""
                        )
                        program = (
                            clean_row.get("Program")
                            or clean_row.get("البرنامج")
                            or clean_row.get("اسم البرنامج")
                            or ""
                        )

                        code = to_english_digits(code)
                        national_id = normalize_national_id(national_id)
                        name = name.strip()
                        program = program.strip()

                        data = {
                            "code": code,
                            "name": name,
                            "national_id": national_id,
                            "program": program
                        }

                        if code:
                            self.database[code] = data
                        if national_id:
                            self.database[national_id] = data

                file_read_success = True
                break

            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                messagebox.showerror("خطأ في قاعدة البيانات", f"تعذر تحميل بيانات الممتحنين:\n{e}")
                return

        if not file_read_success:
            messagebox.showerror(
                "خطأ في القراءة",
                "تعذر قراءة ملف البيانات، يرجى التأكد من حفظه بتنسيق CSV UTF-8."
            )

    def init_daily_log_csv(self):
        if not os.path.exists(self.daily_log_file):
            with open(self.daily_log_file, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "م", 
                    "الترتيب", 
                    "الاسم", 
                    "كود المعلم", 
                    "الرقم القومي", 
                    "البرنامج", 
                    "وقت وتاريخ الوصول", 
                    "التوقيع"
                ])
        else:
            try:
                with open(self.daily_log_file, mode='r', encoding='utf-8-sig') as file:
                    rows = list(csv.reader(file))
                    if len(rows) > 1:
                        self.current_number = len(rows)
            except Exception:
                pass

    def setup_ui(self):
        title_label = tk.Label(
            self.root, 
            text="الأكاديمية المهنية للمعلمين - فرع الجيزة\nنظام إصدار تذاكر أسبقية الحضور", 
            font=("Arial", 14, "bold"), 
            bg="#003366", 
            fg="white", 
            pady=10
        )
        title_label.pack(fill=tk.X)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        top_bar = tk.Frame(frame)
        top_bar.pack(fill=tk.X, pady=(0, 5))
        
        btn_open_log = tk.Button(
            top_bar, 
            text=f"📂 فتح CSV اليوم ({self.today_str})", 
            font=("Arial", 9, "bold"), 
            bg="#8e44ad", 
            fg="white", 
            command=self.open_daily_log
        )
        btn_open_log.pack(side=tk.RIGHT, padx=2)

        btn_export_pdf = tk.Button(
            top_bar, 
            text="📄 استخراج كشف الحضور (PDF)", 
            font=("Arial", 9, "bold"), 
            bg="#2980b9", 
            fg="white", 
            command=self.export_pdf_report
        )
        btn_export_pdf.pack(side=tk.RIGHT, padx=2)

        btn_reprint_ticket = tk.Button(
            top_bar,
            text="🖨 إعادة طباعة تذكرة حاضر",
            font=("Arial", 9, "bold"),
            bg="#16a085",
            fg="white",
            command=self.reprint_attendance_ticket
        )
        btn_reprint_ticket.pack(side=tk.RIGHT, padx=2)

        search_frame = tk.LabelFrame(frame, text=" البحث عن المعلم (فرع الجيزة) ", font=("Arial", 11, "bold"), padx=10, pady=10)
        search_frame.pack(fill=tk.X, pady=5)

        tk.Label(search_frame, text=":ادخل كود المعلم أو الرقم القومي", font=("Arial", 11)).grid(row=0, column=1, sticky="e", padx=5)
        self.entry_search = tk.Entry(search_frame, font=("Arial", 12), justify="center", width=25)
        self.entry_search.grid(row=0, column=0, padx=5, pady=5)
        self.entry_search.bind("<Return>", lambda event: self.search_teacher())

        btn_search = tk.Button(search_frame, text="بحث", font=("Arial", 10, "bold"), bg="#3498db", fg="white", command=self.search_teacher)
        btn_search.grid(row=0, column=2, padx=5)

        info_frame = tk.LabelFrame(frame, text=" بيانات المعلم المسجل ", font=("Arial", 11, "bold"), padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=10)

        self.lbl_code = tk.Label(info_frame, text="كود المعلم: ---", font=("Arial", 11), anchor="e")
        self.lbl_code.pack(fill=tk.X, pady=2)

        self.lbl_name = tk.Label(info_frame, text="الاســــــم: ---", font=("Arial", 11, "bold"), fg="#003366", anchor="e")
        self.lbl_name.pack(fill=tk.X, pady=2)

        self.lbl_id = tk.Label(info_frame, text="الرقم القومي: ---", font=("Arial", 11), anchor="e")
        self.lbl_id.pack(fill=tk.X, pady=2)

        self.lbl_program = tk.Label(info_frame, text="البرنامــــج: ---", font=("Arial", 11), fg="#c0392b", anchor="e")
        self.lbl_program.pack(fill=tk.X, pady=2)

        self.btn_confirm = tk.Button(
            frame, 
            text="تأكيد الحضور وإصدار التذكرة النهائية", 
            font=("Arial", 12, "bold"), 
            bg="#27ae60", 
            fg="white", 
            state=tk.DISABLED,
            command=self.confirm_attendance,
            cursor="hand2"
        )
        self.btn_confirm.pack(fill=tk.X, pady=15)

    def search_teacher(self):
        raw_query = self.entry_search.get().strip()
        query = to_english_digits(raw_query)

        if not query:
            messagebox.showwarning("تنبيه", "يرجى كتابة كود المعلم أو الرقم القومي للبحث.")
            return

        if query in self.database:
            self.selected_teacher = self.database[query]
            self.lbl_code.config(text=f"كود المعلم: {to_english_digits(self.selected_teacher['code'])}")
            self.lbl_name.config(text=f"الاســــــم: {self.selected_teacher['name']}")
            self.lbl_id.config(text=f"الرقم القومي: {normalize_national_id(self.selected_teacher['national_id'])}")
            self.lbl_program.config(text=f"البرنامــــج: {self.selected_teacher['program']}")
            self.btn_confirm.config(state=tk.NORMAL)
        else:
            messagebox.showerror("خطأ", "لم يتم العثور على المعلم في قاعدة البيانات!")
            self.reset_info()

    def confirm_attendance(self):
        if not self.selected_teacher:
            return

        now_str = datetime.datetime.now().strftime("%Y-%m-%d | %I:%M:%S %p")
        ticket_id = f"A-{self.current_number:03d}"

        with open(self.daily_log_file, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow([
                self.current_number,
                ticket_id,
                self.selected_teacher['name'],
                self.selected_teacher['code'],
                self.selected_teacher['national_id'],
                self.selected_teacher['program'],
                now_str,
                ""
            ])

        ticket_file_path = self.generate_formatted_ticket(ticket_id, now_str)
        self.show_ticket_popup(ticket_id, now_str, ticket_file_path)

        self.current_number += 1
        self.entry_search.delete(0, tk.END)
        self.reset_info()

    def load_today_attendance(self):
        if not os.path.exists(self.daily_log_file):
            return []

        rows = []
        try:
            with open(self.daily_log_file, mode="r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    clean = {
                        str(k).strip(): str(v).strip() if v is not None else ""
                        for k, v in row.items()
                        if k is not None
                    }
                    if clean.get("الترتيب") or clean.get("رقم الترتيب") or clean.get("الاسم"):
                        rows.append(clean)
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر قراءة سجل حضور اليوم:\n{e}")
        return rows

    def find_attendance_record(self, query):
        query = to_english_digits(str(query or "")).strip()
        if not query:
            return None

        query_id = normalize_national_id(query)
        rows = self.load_today_attendance()

        for row in rows:
            ticket_id = str(row.get("الترتيب") or row.get("رقم الترتيب") or "").strip()
            code = to_english_digits(row.get("كود المعلم", ""))
            national_id = normalize_national_id(row.get("الرقم القومي", ""))
            name = str(row.get("الاسم", "")).strip()

            if (
                query.lower() == ticket_id.lower()
                or query_id == code
                or query_id == national_id
                or query == name
            ):
                return row

        return None

    def create_ticket_from_attendance_record(self, row):
        ticket_id = str(row.get("الترتيب") or row.get("رقم الترتيب") or "").strip()
        if not ticket_id:
            return None, None

        self.selected_teacher = {
            "name": str(row.get("الاسم", "")).strip(),
            "program": str(row.get("البرنامج", "")).strip(),
            "national_id": normalize_national_id(row.get("الرقم القومي", "")),
            "code": to_english_digits(row.get("كود المعلم", ""))
        }

        now_str = str(row.get("وقت وتاريخ الوصول", "")).strip()
        file_path = self.generate_formatted_ticket(ticket_id, now_str)
        return ticket_id, file_path

    def reprint_attendance_ticket(self):
        rows = self.load_today_attendance()

        if not rows:
            messagebox.showinfo(
                "لا يوجد حضور",
                "لا يوجد أي ممتحنين مسجلين كحاضرين اليوم، لذلك لا توجد تذكرة لإعادة طباعتها."
            )
            return

        popup = tk.Toplevel(self.root)
        popup.title("إعادة طباعة تذكرة حضور")
        popup.geometry("520x360")
        popup.resizable(False, False)

        tk.Label(
            popup,
            text="إعادة طباعة تذكرة لمن حضر بالفعل",
            font=("Arial", 13, "bold"),
            fg="#003366"
        ).pack(pady=(15, 5))

        tk.Label(
            popup,
            text="يمكن البحث بالترتيب أو كود المعلم أو الرقم القومي أو الاسم",
            font=("Arial", 10)
        ).pack(pady=5)

        search_frame = tk.Frame(popup)
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        entry = tk.Entry(search_frame, font=("Arial", 12), justify="center")
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        entry.focus_set()

        result_frame = tk.LabelFrame(
            popup,
            text="بيانات الحضور",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
        result_frame.pack(fill=tk.X, padx=20, pady=5)

        result_label = tk.Label(
            result_frame,
            text="أدخل بيانات البحث ثم اضغط بحث",
            font=("Arial", 10),
            justify="right",
            anchor="e"
        )
        result_label.pack(fill=tk.X)

        selected_row = {"value": None}

        def do_search():
            row = self.find_attendance_record(entry.get())
            selected_row["value"] = row

            if row:
                ticket_val = row.get('الترتيب') or row.get('رقم الترتيب', '')
                result_label.config(
                    text=(
                        f"الاسم: {row.get('الاسم', '')}\n"
                        f"الترتيب: {ticket_val}\n"
                        f"كود المعلم: {row.get('كود المعلم', '')}\n"
                        f"الرقم القومي: {normalize_national_id(row.get('الرقم القومي', ''))}\n"
                        f"وقت الحضور: {row.get('وقت وتاريخ الوصول', '')}"
                    ),
                    fg="#1a252f"
                )
                btn_print.config(state=tk.NORMAL)
            else:
                result_label.config(
                    text="لم يتم العثور على شخص مسجل كحاضر اليوم بهذه البيانات.",
                    fg="#c0392b"
                )
                btn_print.config(state=tk.DISABLED)

        def do_print():
            row = selected_row["value"]
            if not row:
                return

            ticket_id, file_path = self.create_ticket_from_attendance_record(row)
            if not file_path:
                messagebox.showerror("خطأ", "تعذر إنشاء التذكرة.")
                return

            self.print_ticket(file_path)

        btn_search = tk.Button(
            search_frame,
            text="بحث",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=do_search
        )
        btn_search.pack(side=tk.LEFT, padx=5)

        entry.bind("<Return>", lambda event: do_search())

        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)

        btn_print = tk.Button(
            btn_frame,
            text="🖨 طباعة التذكرة",
            font=("Arial", 11, "bold"),
            bg="#003366",
            fg="white",
            state=tk.DISABLED,
            command=do_print
        )
        btn_print.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        btn_close = tk.Button(
            btn_frame,
            text="إغلاق",
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            command=popup.destroy
        )
        btn_close.pack(side=tk.LEFT, padx=5)

    def export_pdf_report(self):
        output_pdf = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"كشف_حضور_{self.today_str}.pdf"
        )

        rows = self.load_today_attendance()

        attendance = []
        for row in rows:
            clean = {
                "م": str(row.get("م", "") or "").strip(),
                "الترتيب": str(row.get("الترتيب") or row.get("رقم الترتيب") or "").strip(),
                "الاسم": str(row.get("الاسم", "") or "").strip(),
                "كود المعلم": to_english_digits(row.get("كود المعلم", "")),
                "الرقم القومي": normalize_national_id(row.get("الرقم القومي", "")),
                "البرنامج": str(row.get("البرنامج", "") or "").strip(),
                "وقت وتاريخ الوصول": str(row.get("وقت وتاريخ الوصول", "") or "").strip(),
                "التوقيع": str(row.get("التوقيع", "") or "").strip()
            }
            if clean["الترتيب"]:
                attendance.append(clean)

        try:
            display_date = datetime.datetime.strptime(
                self.today_str, "%Y-%m-%d"
            ).strftime("%d-%m-%Y")
        except Exception:
            display_date = self.today_str

        doc = SimpleDocTemplate(
            output_pdf,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=15,
            bottomMargin=25
        )

        story = []

        header_right_style = ParagraphStyle(
            "HeaderRight",
            fontName="ArabicFont-Bold",
            fontSize=11,
            leading=13,
            alignment=2,
            textColor=colors.HexColor("#003366")
        )

        date_left_style = ParagraphStyle(
            "DateLeft",
            fontName="ArabicFont-Bold",
            fontSize=10,
            leading=12,
            alignment=0,
            textColor=colors.black
        )

        title_style = ParagraphStyle(
            "DocTitle",
            fontName="ArabicFont-Bold",
            fontSize=15,
            leading=19,
            alignment=1,
            textColor=colors.HexColor("#003366"),
            spaceBefore=2,
            spaceAfter=6
        )

        cell_style = ParagraphStyle(
            "TableCell",
            fontName="ArabicFont",
            fontSize=11,
            leading=13,
            alignment=1
        )

        # تنسيق مصغر خاص بخلية الوقت والتاريخ لمنع الالتفاف
        date_cell_style = ParagraphStyle(
            "DateTableCell",
            fontName="ArabicFont",
            fontSize=9.5,
            leading=11,
            alignment=1
        )

        cell_bold_style = ParagraphStyle(
            "TableCellBold",
            fontName="ArabicFont-Bold",
            fontSize=11,
            leading=13,
            alignment=1
        )

        th_style = ParagraphStyle(
            "TableHeader",
            fontName="ArabicFont-Bold",
            fontSize=11.5,
            leading=14,
            alignment=1,
            textColor=colors.white
        )

        footer_sign_style = ParagraphStyle(
            "FooterSign",
            fontName="ArabicFont-Bold",
            fontSize=11,
            leading=15,
            alignment=1
        )

        display_columns = [
            "التوقيع",
            "وقت وتاريخ الوصول",
            "البرنامج",
            "الرقم القومي",
            "كود المعلم",
            "الاسم",
            "الترتيب",
            "م"
        ]

        # عرض الأعمدة: توسيع التوقيع إلى 135 وضبط وقت الوصول إلى 95
        col_widths = [135, 95, 100, 100, 75, 145, 52, 28]
        rows_per_page = 19

        page_chunks = [
            attendance[i:i + rows_per_page]
            for i in range(0, len(attendance), rows_per_page)
        ]

        if not page_chunks:
            page_chunks = [[]]

        for page_index, chunk in enumerate(page_chunks):
            header_text = Paragraph(fix_arabic("الأكاديمية المهنية للمعلمين - فرع الجيزة"), header_right_style)
            date_text = Paragraph(fix_arabic(f"التاريخ: {display_date}"), date_left_style)

            top_header_table = Table([[date_text, header_text]], colWidths=[365, 365])
            top_header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(top_header_table)

            story.append(
                Paragraph(
                    fix_arabic(f"كشف إثبات حضور المعلمين ({display_date})"),
                    title_style
                )
            )

            headers_formatted = [
                fix_arabic("التوقيع"),
                fix_arabic("وقت وتاريخ الوصول"),
                fix_arabic("البرنامج"),
                fix_arabic("الرقم القومي"),
                fix_arabic("كود المعلم"),
                fix_arabic("الاسم"),
                fix_arabic("الترتيب"),
                fix_arabic("م")
            ]

            table_data = [
                [Paragraph(col, th_style) for col in headers_formatted]
            ]

            for local_index in range(rows_per_page):
                global_index = page_index * rows_per_page + local_index
                row = chunk[local_index] if local_index < len(chunk) else None
                serial_no = global_index + 1

                if row:
                    values = {
                        "التوقيع": "",
                        "وقت وتاريخ الوصول": row["وقت وتاريخ الوصول"],
                        "البرنامج": row["البرنامج"],
                        "الرقم القومي": row["الرقم القومي"],
                        "كود المعلم": row["كود المعلم"],
                        "الاسم": row["الاسم"],
                        "الترتيب": row["الترتيب"],
                        "م": str(serial_no)
                    }
                else:
                    values = {
                        "التوقيع": "",
                        "وقت وتاريخ الوصول": "",
                        "البرنامج": "",
                        "الرقم القومي": "",
                        "كود المعلم": "",
                        "الاسم": "",
                        "الترتيب": "",
                        "م": str(serial_no)
                    }

                row_data = []
                for col in display_columns:
                    if col == "وقت وتاريخ الوصول":
                        style_to_use = date_cell_style
                    elif col in ["م", "الترتيب"]:
                        style_to_use = cell_bold_style
                    else:
                        style_to_use = cell_style
                        
                    row_data.append(Paragraph(fix_arabic(values[col]), style_to_use))

                table_data.append(row_data)

            row_heights = [26] + [22] * rows_per_page

            main_table = Table(
                table_data,
                colWidths=col_widths,
                rowHeights=row_heights,
                repeatRows=1,
                hAlign="CENTER"
            )

            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A3161")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A6ACAF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]

            main_table.setStyle(TableStyle(table_style))
            story.append(main_table)

            story.append(Paragraph("<br/>", cell_style))
            
            sign_cols = [
                Paragraph(f"{fix_arabic('مدير إدارة الفرع')}<br/>.......................", footer_sign_style),
                Paragraph(f"{fix_arabic('مسئول المعمل')}<br/>.......................", footer_sign_style),
                Paragraph(f"{fix_arabic('المختص')}<br/>.......................", footer_sign_style)
            ]
            
            signatures_table = Table([sign_cols], colWidths=[240, 250, 240])
            signatures_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            
            story.append(signatures_table)

            if page_index < len(page_chunks) - 1:
                story.append(Paragraph("<br/>", cell_style))

        try:
            doc.build(story, canvasmaker=NumberedCanvas)
            messagebox.showinfo(
                "نجاح",
                f"تم إنشاء كشف الحضور بنجاح!\n"
                f"عدد التذاكر المدرجة: {len(attendance)}\n"
                f"المسار:\n{output_pdf}"
            )
            os.startfile(output_pdf)

        except Exception as e:
            messagebox.showerror(
                "خطأ في الإنشاء",
                f"تعذر استخراج كشف الحضور PDF:\n{e}"
            )

    def generate_formatted_ticket(self, ticket_id, now_str):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        safe_ticket_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(ticket_id))
        file_path = os.path.join(base_dir, f"ticket_{safe_ticket_id}.html")

        name = html.escape(str(self.selected_teacher.get("name", "")))
        program = html.escape(str(self.selected_teacher.get("program", "")))
        national_id = html.escape(normalize_national_id(self.selected_teacher.get("national_id", "")))
        code = html.escape(to_english_digits(self.selected_teacher.get("code", "")))
        ticket = html.escape(str(ticket_id))
        date_time = html.escape(str(now_str))

        name_len = len(html.unescape(name))
        program_len = len(html.unescape(program))
        id_len = len(html.unescape(national_id))

        name_size = 17 if name_len <= 22 else 15 if name_len <= 32 else 13
        program_size = 15 if program_len <= 24 else 13 if program_len <= 38 else 11.5
        id_size = 14 if id_len <= 14 else 12.5 if id_len <= 18 else 11.5

        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=100mm, initial-scale=1.0">
<title>تذكرة رقم {ticket}</title>
<style>
    @page {{
        size: 100mm 150mm;
        margin: 0 !important;
    }}

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    html, body {{
        width: 100mm;
        height: 150mm;
        background: #f0f0f0;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: Arial, "Segoe UI", Tahoma, sans-serif;
        direction: rtl;
        overflow: hidden;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .page-container {{
        width: 100mm;
        height: 150mm;
        display: flex;
        justify-content: center;
        align-items: center;
    }}

    .ticket-card {{
        width: 90mm;
        padding: 4mm;
        border: 1.2px solid #003366;
        border-radius: 3mm;
        background: #ffffff;
        text-align: center;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin: auto;
    }}

    .header {{
        padding-bottom: 2.5mm;
        margin-bottom: 2mm;
        border-bottom: 1.5px solid #003366;
    }}

    .academy {{
        margin: 0;
        color: #003366;
        font-size: 15px;
        line-height: 1.2;
        font-weight: 700;
    }}

    .branch {{
        margin: 1mm 0 0;
        color: #555555;
        font-size: 11.5px;
        font-weight: 700;
    }}

    .ticket-title {{
        margin: 1mm 0 1mm;
        color: #555555;
        font-size: 11px;
        font-weight: 700;
    }}

    .ticket-number {{
        display: block;
        width: 100%;
        margin: 0 auto 2.5mm;
        padding: 1.5mm 2mm;
        border: 1.5px dashed #c0392b;
        border-radius: 2mm;
        background: #fff8e8;
        color: #c0392b;
        font-size: 28px;
        line-height: 1;
        font-weight: 900;
        letter-spacing: 0.5px;
    }}

    .info-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        margin: 0 0 2mm;
        direction: rtl;
    }}

    .info-table td {{
        padding: 1.2mm 0.8mm;
        vertical-align: middle;
        border-bottom: 0.7px solid #e5e5e5;
    }}

    .info-label {{
        width: 32%;
        color: #333333;
        font-size: 10px;
        font-weight: 700;
        text-align: right;
        white-space: nowrap;
    }}

    .info-val {{
        width: 68%;
        color: #000000;
        font-weight: 700;
        text-align: right;
        direction: rtl;
        overflow-wrap: anywhere;
        word-break: break-word;
    }}

    .name-value {{
        font-size: {name_size}px;
    }}

    .program-value {{
        font-size: {program_size}px;
    }}

    .national-id-value {{
        font-size: {id_size}px;
        direction: ltr;
        text-align: right;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }}

    .code-value {{
        font-size: 12.5px;
        direction: ltr;
        text-align: right;
        white-space: nowrap;
    }}

    .date-value {{
        font-size: 9.5px;
        direction: ltr;
        text-align: right;
        white-space: nowrap;
    }}

    .requirements {{
        width: 100%;
        margin-top: 1.5mm;
        padding: 2mm;
        border: 1.2px solid #d5dbdb;
        border-radius: 2mm;
        background: #f7f8f8;
        text-align: right;
    }}

    .requirements-title {{
        margin: 0 0 1.2mm;
        color: #c0392b;
        font-size: 12px;
        font-weight: 900;
        text-align: center;
    }}

    .requirements ul {{
        margin: 0;
        padding: 0 4mm 0 0;
        color: #1a252f;
        font-size: 10.5px;
        line-height: 1.35;
        font-weight: 700;
    }}

    .requirements li {{
        margin: 0 0 1mm;
    }}

    .footer {{
        margin-top: 2.5mm;
        padding-top: 1.5mm;
        border-top: 1.2px solid #003366;
        color: #0e6251;
        font-size: 11px;
        line-height: 1.2;
        font-weight: 900;
    }}

    @media print {{
        html, body {{
            width: 100mm !important;
            height: 150mm !important;
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }}

        .page-container {{
            width: 100mm !important;
            height: 150mm !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }}

        .ticket-card {{
            border: 1px solid #000000;
            box-shadow: none !important;
        }}
    }}
</style>
</head>
<body>
<div class="page-container">
    <div class="ticket-card">

        <div class="header">
            <div class="academy">الأكاديمية المهنية للمعلمين</div>
            <div class="branch">فرع الجيزة</div>
        </div>

        <div class="ticket-title">تذكرة أسبقية الحضور</div>
        <div class="ticket-number">[ {ticket} ]</div>

        <table class="info-table">
            <tr>
                <td class="info-label">الاسم:</td>
                <td class="info-val name-value">{name}</td>
            </tr>
            <tr>
                <td class="info-label">البرنامج:</td>
                <td class="info-val program-value">{program}</td>
            </tr>
            <tr>
                <td class="info-label">الرقم القومي:</td>
                <td class="info-val national-id-value">{national_id}</td>
            </tr>
            <tr>
                <td class="info-label">كود المعلم:</td>
                <td class="info-val code-value">{code}</td>
            </tr>
            <tr>
                <td class="info-label">التاريخ والوقت:</td>
                <td class="info-val date-value">{date_time}</td>
            </tr>
        </table>

        <div class="requirements">
            <div class="requirements-title">⚠ تنبيه هام - مستندات مطلوبة</div>
            <ul>
                <li>صحيفة أحوال الكترونية حديثة.</li>
                <li>صورة العقد بالنسبة للمعلم المساعد.</li>
                <li>صورة بطاقة الرقم القومي سارية.</li>
                <li>إيصال الدفع إن وجد.</li>
            </ul>
        </div>

        <div class="footer">
            أهلاً بكم في فرع الجيزة - يرجى الانتظار لحين استدعائكم
        </div>

    </div>
</div>
</body>
</html>
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def show_ticket_popup(self, ticket_id, now_str, file_path):
        popup = tk.Toplevel(self.root)
        popup.title(f"التذكرة النهائية {ticket_id}")
        popup.geometry("480x760")
        popup.resizable(False, False)

        tk.Label(popup, text="تم تسجيل الحضور وإصدار التذكرة بنجاح", font=("Arial", 11, "bold"), fg="#27ae60", pady=6).pack()

        outer_frame = tk.Frame(popup, bg="#003366", bd=2, relief="solid")
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        inner_frame = tk.Frame(outer_frame, bg="white", padx=12, pady=8)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(inner_frame, text="الأكاديمية المهنية للمعلمين", font=("Arial", 12, "bold"), bg="white", fg="#003366").pack(pady=1)
        tk.Label(inner_frame, text="فرع الجيزة", font=("Arial", 10, "bold"), bg="white", fg="#555").pack(pady=0)
        
        ttk.Separator(inner_frame, orient='horizontal').pack(fill='x', pady=5)

        tk.Label(inner_frame, text="تذكرة أسبقية الحضور", font=("Arial", 10), bg="white").pack()
        tk.Label(inner_frame, text=f"[ {ticket_id} ]", font=("Arial", 20, "bold"), bg="white", fg="#c0392b").pack(pady=3)

        ttk.Separator(inner_frame, orient='horizontal').pack(fill='x', pady=5)

        data_frame = tk.Frame(inner_frame, bg="white")
        data_frame.pack(fill=tk.X, pady=3)

        details = [
            ("الاســــــم :", self.selected_teacher['name']),
            ("البرنامــــج :", self.selected_teacher['program']),
            ("الرقم القومي :", self.selected_teacher['national_id']),
            ("كود المعلم :", self.selected_teacher['code']),
            ("الوقت والتاريخ :", now_str)
        ]

        for lbl_text, val_text in details:
            row = tk.Frame(data_frame, bg="white")
            row.pack(fill=tk.X, pady=2)
            
            lbl_val = tk.Label(
                row, 
                text=val_text, 
                font=("Arial", 9, "bold"), 
                bg="white", 
                fg="#000000", 
                anchor="e", 
                justify="right"
            )
            lbl_val.pack(side=tk.RIGHT, fill=tk.X, expand=True)

            lbl_title = tk.Label(
                row, 
                text=lbl_text, 
                font=("Arial", 9, "bold"), 
                bg="white", 
                fg="#333333", 
                anchor="e", 
                justify="right"
            )
            lbl_title.pack(side=tk.RIGHT, padx=(5, 0))

        req_frame = tk.LabelFrame(inner_frame, text=" ⚠️ تنبيه هام ومستندات مطلوبة ", font=("Arial", 10, "bold"), bg="white", fg="#c0392b", padx=5, pady=5)
        req_frame.pack(fill=tk.X, pady=5)

        reqs = [
            "• يرجى تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.",
            "• صورة بطاقة الرقم القومي سارية.",
            "• إيصال الدفع إن وجد."
        ]
        for req in reqs:
            tk.Label(req_frame, text=req, font=("Arial", 9, "bold"), bg="white", fg="#1a252f", anchor="e", justify="right").pack(fill=tk.X, anchor="e")

        ttk.Separator(inner_frame, orient='horizontal').pack(fill='x', pady=5)

        tk.Label(inner_frame, text="أهلاً بكم في فرع الجيزة - يرجى الانتظار لحين استدعائكم", font=("Arial", 10, "bold"), bg="white", fg="#0e6251").pack(pady=3)

        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill=tk.X, pady=10)

        btn_print = tk.Button(btn_frame, text="طباعة التذكرة", font=("Arial", 10, "bold"), bg="#003366", fg="white", command=lambda: self.print_ticket(file_path))
        btn_print.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        btn_open = tk.Button(btn_frame, text="عرض التذكرة بالكامل", font=("Arial", 10), bg="#27ae60", fg="white", command=lambda: webbrowser.open(file_path))
        btn_open.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        btn_close = tk.Button(btn_frame, text="إغلاق", font=("Arial", 10), bg="#e74c3c", fg="white", command=popup.destroy)
        btn_close.pack(side=tk.RIGHT, padx=10)

    def print_ticket(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("خطأ", f"لم يتم العثور على ملف التذكرة:\n{file_path}")
            return

        try:
            os.startfile(file_path, "print")
        except Exception:
            try:
                webbrowser.open(file_path)
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر إرسال التذكرة للطباعة: {e}")

    def open_daily_log(self):
        if os.path.exists(self.daily_log_file):
            os.startfile(self.daily_log_file)
        else:
            messagebox.showinfo("تنبيه", "لم يتم تسجيل أي حضور حتى الآن لليوم.")

    def reset_info(self):
        self.selected_teacher = None
        self.lbl_code.config(text="كود المعلم: ---")
        self.lbl_name.config(text="الاســــــم: ---")
        self.lbl_id.config(text="الرقم القومي: ---")
        self.lbl_program.config(text="البرنامــــج: ---")
        self.btn_confirm.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = PATGizaQueueSystem(root)
    root.mainloop()
