import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title=(
        "الأكاديمية المهنية للمعلمين - فرع الجيزة | نظام أسبقية الحضور"
    ),
    page_icon="🏛️",
    layout="centered",
)

# تنسيقات الواجهة العامة
st.markdown(
    """
    <style>
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #f8f9fa;
    }
    .stSidebar {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# أسماء ملفات البيانات
TEACHERS_FILE = "teachers_database.csv"
LOG_FILE = "attendance_log_giza.csv"


def init_files():
  if not os.path.exists(TEACHERS_FILE):
    df_default = pd.DataFrame(
        columns=[
            "Code",
            "Name",
            "National_ID",
            "Program",
            "School",
            "Administration",
            "Phone",
            "Job_Title",
        ]
    )
    df_default.to_csv(TEACHERS_FILE, index=False, encoding="utf-8-sig")

  if not os.path.exists(LOG_FILE):
    log_default = pd.DataFrame(
        columns=[
            "National_ID",
            "Name",
            "School",
            "Program",
            "Code_ID",
            "Date",
            "Time",
            "Status",
        ]
    )
    log_default.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")


init_files()

# العنوان العلوي مطابق لبرنامج الجهاز
st.markdown(
    "<h3 style='text-align: center; color: #10233F;'>الأكاديمية المهنية للمعلمين"
    " - فرع الجيزة</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: #333; font-size: 16px;'>نظام إصدار"
    " تذاكر أسبقية الحضور</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

# القائمة الجانبية للتنقل
menu = ["إصدار التذاكر والحضور", "إدارة المعلمين", "سجل الحضور والتقارير"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)


@st.cache_data(ttl=2)
def load_data():
  teachers_df = None
  for enc in ["utf-8-sig", "utf-8", "cp1256", "iso-8859-6", "latin1"]:
    try:
      teachers_df = pd.read_csv(
          TEACHERS_FILE, dtype=str, encoding=enc, sep=";"
      )
      if len(teachers_df.columns) <= 1:
        teachers_df = pd.read_csv(
            TEACHERS_FILE, dtype=str, encoding=enc, sep=","
        )
      break
    except:
      continue

  if teachers_df is None or teachers_df.empty:
    teachers_df = pd.DataFrame(
        columns=[
            "Code",
            "Name",
            "National_ID",
            "Program",
            "School",
            "Administration",
            "Phone",
            "Job_Title",
        ]
    )

  teachers_df.columns = [c.strip() for c in teachers_df.columns]

  log_df = None
  for enc in ["utf-8-sig", "utf-8", "cp1256", "iso-8859-6", "latin1"]:
    try:
      log_df = pd.read_csv(LOG_FILE, dtype=str, encoding=enc, sep=",")
      break
    except:
      try:
        log_df = pd.read_csv(LOG_FILE, dtype=str, encoding=enc, sep=";")
        break
      except:
        continue

  expected_log_cols = [
      "National_ID",
      "Name",
      "School",
      "Program",
      "Code_ID",
      "Date",
      "Time",
      "Status",
  ]
  if log_df is None or len(log_df.columns) < len(expected_log_cols):
    log_df = pd.DataFrame(columns=expected_log_cols)
    log_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

  log_df.columns = [c.strip() for c in log_df.columns]
  for col in expected_log_cols:
    if col not in log_df.columns:
      log_df[col] = ""

  return teachers_df, log_df


teachers_df, log_df = load_data()

# 1. صفحة إصدار التذاكر والحضور
if choice == "إصدار التذاكر والحضور":

  st.markdown("### البحث عن المعلم (فرع الجيزة)")
  col_search1, col_search2 = st.columns([3, 1])
  with col_search1:
    search_input = st.text_input(
        "ادخل كود المعلم أو الرقم القومي:",
        placeholder="أدخل الكود أو الرقم القومي...",
        key="search_query",
        label_visibility="collapsed",
    )
  with col_search2:
    search_btn = st.button("بحث", type="primary", use_container_width=True)

  st.markdown("---")

  found_teacher = None
  if search_btn or search_input:
    query = search_input.strip()
    if query:
      id_col = (
          "National_ID"
          if "National_ID" in teachers_df.columns
          else teachers_df.columns[2]
      )
      code_col = (
          "Code" if "Code" in teachers_df.columns else teachers_df.columns[0]
      )

      res = teachers_df[
          (teachers_df[id_col].astype(str).str.strip() == query)
          | (teachers_df[code_col].astype(str).str.strip() == query)
      ]
      if not res.empty:
        found_teacher = res.iloc[0]
      else:
        st.warning(
            "لم يتم العثور على المعلم. تأكد من صحة الكود أو الرقم القومي، أو قم"
            " بإضافته من قائمة 'إدارة المعلمين'."
        )

  st.markdown("### بيانات المعلم المسجل")
  with st.container():
    if found_teacher is not None:
      t_code = (
          found_teacher.get("Code", "---")
          if "Code" in found_teacher
          else "3695367"
      )
      t_name = (
          found_teacher.get("Name", "---")
          if "Name" in found_teacher
          else "أحمد مجدي محمد عبد القادر"
      )
      t_id = (
          found_teacher.get("National_ID", "---")
          if "National_ID" in found_teacher
          else "29610092101373"
      )
      t_prog = (
          found_teacher.get("Program", "تطبيقات تربوية للمعلم المساعد")
          if "Program" in found_teacher
          else "تطبيقات تربوية للمعلم المساعد"
      )

      st.markdown(f"**كود المعلم:** {t_code}")
      st.markdown(f"**الاسم:** {t_name}")
      st.markdown(f"**الرقم القومي:** {t_id}")
      st.markdown(f"**البرنامج:** {t_prog}")

      st.session_state["current_selected_teacher"] = {
          "code": t_code,
          "name": t_name,
          "id": t_id,
          "program": t_prog,
      }
    else:
      st.markdown("كود المعلم: ---")
      st.markdown("الاسم: ---")
      st.markdown("الرقم القومي: ---")
      st.markdown("البرنامج: ---")

  st.markdown("---")

  if st.button(
      "تأكيد الحضور وإصدار التذكرة النهائية",
      type="primary",
      use_container_width=True,
  ):
    if "current_selected_teacher" in st.session_state:
      ft = st.session_state["current_selected_teacher"]

      # ضبط الوقت والتاريخ حسب توقيت مصر المحلي (القاهرة) بدقة تامة
      cairo_tz = ZoneInfo("Africa/Cairo")
      current_date = datetime.now(cairo_tz).strftime("%Y-%m-%d")
      current_time = datetime.now(cairo_tz).strftime("%I:%M:%S %p")

      already_logged = log_df[
          (log_df["National_ID"].astype(str).str.strip() == str(ft["id"]))
          & (log_df["Date"] == current_date)
      ]

      if not already_logged.empty:
        serial_no = already_logged.iloc[0].get("Code_ID", "A-001")
        st.info(f"المعلم/ـة **{ft['name']}** مسجل مسبقاً لهذا اليوم.")
        st.session_state["show_ticket_modal"] = {
            "name": ft["name"],
            "program": ft["program"],
            "id": ft["id"],
            "code": ft["code"],
            "serial": serial_no,
            "datetime": f"{current_date} | {already_logged.iloc[0]['Time']}",
        }
      else:
        today_logs = log_df[log_df["Date"] == current_date]
        serial_num = len(today_logs) + 1
        serial_str = f"A-{serial_num:03d}"

        t_real_code = ft["code"]
        match_t = teachers_df[
            teachers_df["National_ID"].astype(str).str.strip()
            == str(ft["id"])
        ]
        if not match_t.empty and "Code" in match_t.columns:
          t_real_code = str(match_t.iloc[0]["Code"])

        new_entry = pd.DataFrame(
            [{
                "National_ID": ft["id"],
                "Name": ft["name"],
                "School": "فرع الجيزة",
                "Program": ft["program"],
                "Code_ID": serial_str,
                "Date": current_date,
                "Time": current_time,
                "Status": "حاضر",
                "Teacher_Code": t_real_code,
            }]
        )
        log_df = pd.concat([log_df, new_entry], ignore_index=True)
        log_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

        st.success(
            f"تم تسجيل الحضور وإصدار التذكرة بنجاح برقم الأسبقية:"
            f" **{serial_str}**"
        )
        st.session_state["show_ticket_modal"] = {
            "name": ft["name"],
            "program": ft["program"],
            "id": ft["id"],
            "code": t_real_code,
            "serial": serial_str,
            "datetime": f"{current_date} | {current_time}",
        }
    else:
      st.warning("الرجاء البحث عن المعلم أولاً قبل تأكيد الحضور.")

  # عرض التذكرة
  if "show_ticket_modal" in st.session_state:
    tk = st.session_state["show_ticket_modal"]
    st.markdown("---")
    st.success("تم تسجيل الحضور وإصدار التذكرة بنجاح")

    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
      with st.container(border=True):
        if os.path.exists("Logo.png"):
          st.image("Logo.png", width=110)
        st.markdown(
            "<h4 style='text-align: center; color: #10233F; margin-top:5px;'>الأكاديمية"
            " المهنية للمعلمين</h4>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #555; font-size: 14px;"
            " margin-bottom:5px;'>فرع الجيزة</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; font-size: 12px; color:"
            " #666;'>تذكرة أسبقية الحضور</p>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='text-align: center; background-color: #fdf8e2; border:"
            " 1.5px dashed #C9A227; padding: 10px; border-radius: 8px; margin:"
            " 10px 0;'><span style='font-size: 24px; font-weight: bold; color:"
            f" #d9534f;'>[ {tk['serial']} ]</span></div>",
            unsafe_allow_html=True,
        )

        st.markdown(f"**الاسم:** {tk['name']}")
        st.markdown(f"**البرنامج:** {tk['program']}")
        st.markdown(f"**الرقم القومي:** {tk['id']}")
        st.markdown(f"**كود المعلم:** {tk['code']}")
        st.markdown(f"**الوقت والتاريخ:** {tk['datetime']}")

        st.markdown("---")
        st.warning(
            "⚠️ تنبيه هام ومستندات مطلوبة:\n\n"
            "• تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.\n"
            "• صورة بطاقة الرقم القومي سارية.\n"
            "• إيصال الدفع إن وجد."
        )

        st.markdown(
            "<p style='text-align: center; font-size: 12px; color: #10233F;"
            " font-weight: bold; margin-top: 10px;'>أهلاً بكم في فرع الجيزة - يرجى"
            " الانتظار لحين استدعائكم</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    import base64

    logo_base64 = ""
    if os.path.exists("Logo.png"):
      with open("Logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")

    logo_img_tag = (
        f'<img src="data:image/png;base64,{logo_base64}"'
        ' style="max-height: 85px; display: block; margin: 0 auto 5px auto;" />'
        if logo_base64
        else '<div style="text-align: center; font-size: 28px;">🏛️</div>'
    )

    standalone_ticket_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>تذكرة الحضور - {tk['serial']}</title>
    <style>
        @page {{ size: 10cm 15cm; margin: 0; }}
        body {{ font-family: 'Tahoma', 'Arial', sans-serif; background: #ffffff; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 0; }}
        .ticket-box {{ width: 10cm; height: 15cm; padding: 7mm 9mm; box-sizing: border-box; border: 2.5px solid #10233F; background-color: #ffffff; text-align: right; display: flex; flex-direction: column; justify-content: space-between; }}
        .actions {{ position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); display: flex; justify-content: center; }}
        .btn {{ background-color: #ff4b4b; color: white; padding: 10px 25px; border: none; border-radius: 6px; font-size: 15px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
        @media print {{ .actions {{ display: none; }} body {{ background: white; margin: 0; }} .ticket-box {{ border: 2.5px solid #10233F; width: 10cm; height: 15cm; padding: 6mm 8mm; box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="ticket-box">
        <div>
            {logo_img_tag}
            <div style="text-align: center; color: #10233F; font-weight: bold; font-size: 19px; margin-top: 2px;">الأكاديمية المهنية للمعلمين</div>
            <div style="text-align: center; color: #555; font-size: 14px; margin-bottom: 5px;">فرع الجيزة</div>
            <hr style="border: 1px solid #10233F; margin: 6px 0;">
            <div style="text-align: center; font-size: 12px; color: #666; margin-bottom: 3px;">تذكرة أسبقية الحضور</div>
            <div style="text-align: center; background-color: #fdf8e2; border: 1.5px dashed #C9A227; padding: 7px; border-radius: 6px; margin: 6px 0;">
                <span style="font-size: 26px; font-weight: bold; color: #d9534f;">[ {tk['serial']} ]</span>
            </div>
            <div style="font-size: 13.5px; line-height: 2.2; color: #111; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 6px 0; margin-bottom: 8px;">
                <b>الاسم:</b> {tk['name']}<br>
                <b>البرنامج:</b> {tk['program']}<br>
                <b>الرقم القومي:</b> {tk['id']}<br>
                <b>كود المعلم:</b> {tk['code']}<br>
                <b>الوقت والتاريخ:</b> {tk['datetime']}
            </div>
            <div style="border: 1px solid #e0a800; background-color: #fff3cd; color: #856404; padding: 8px; border-radius: 5px; font-size: 11px; line-height: 1.6; margin-bottom: 8px;">
                <b>⚠️ تنبيه هام ومستندات مطلوبة:</b><br>
                • تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.<br>
                • صورة بطاقة الرقم القومي سارية.<br>
                • إيصال الدفع إن وجد.
            </div>
            <div style="text-align: center; font-size: 12.5px; color: #10233F; font-weight: bold; background-color: #eef2f7; padding: 7px; border-radius: 5px;">
                أهلاً بكم في فرع الجيزة - يرجى الانتظار لحين استدعائكم
            </div>
        </div>
    </div>
    <div class="actions">
        <button class="btn" onclick="window.print()">🖨️ طباعة التذكرة</button>
    </div>
</body>
</html>"""

    popup_button_html = f"""
        <script>
        function openTicketWindow() {{
            var htmlContent = {repr(standalone_ticket_html)};
            var blob = new Blob([htmlContent], {{ type: 'text/html;charset=utf-8' }});
            var blobUrl = URL.createObjectURL(blob);
            var win = window.open(blobUrl, '_blank', 'width=480,height=700,scrollbars=yes');
        }}
        </script>
        <button onclick="openTicketWindow()" style="width: 100%; background-color: #28a745; color: white; padding: 12px 20px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; font-family: 'Tahoma', sans-serif;">
            🌐 فتح التذكرة في نافذة منفصلة للطباعة
        </button>
        """

    b_col1, b_col2 = st.columns(2)
    with b_col1:
      if st.button("إغلاق وإصدار تذكرة جديدة", use_container_width=True):
        if "show_ticket_modal" in st.session_state:
          del st.session_state["show_ticket_modal"]
        if "current_selected_teacher" in st.session_state:
          del st.session_state["current_selected_teacher"]
        st.rerun()
    with b_col2:
      components.html(popup_button_html, height=60)

# 2. صفحة إدارة المعلمين
elif choice == "إدارة المعلمين":
  st.header("👥 قاعدة بيانات المعلمين")

  with st.expander("➕ إضافة معلم جديد"):
    with st.form("add_teacher_form"):
      new_code = st.text_input("كود المعلم", value="3695367")
      new_name = st.text_input("الاسم الكامل")
      new_id = st.text_input("الرقم القومي (14 رقم)", max_chars=14)
      new_prog = st.text_input(
          "اسم البرنامج التدريبي", value="تطبيقات تربوية للمعلم المساعد"
      )
      new_school = st.text_input("المدرسة / الجهة")
      new_admin = st.text_input("الإدارة التعليمية")
      new_phone = st.text_input("رقم الهاتف")
      new_job = st.text_input("الوظيفة")

      submit_button = st.form_submit_button(
          "حفظ وإضافة المعلم", type="primary"
      )

      if submit_button:
        id_col = (
            "National_ID"
            if "National_ID" in teachers_df.columns
            else teachers_df.columns[2]
        )
        if len(new_id) != 14 or not new_id.isdigit() or not new_name:
          st.error(
              "الرجاء التأكد من صحة الرقم القومي (14 رقماً) وإدخال الاسم على"
              " الأقل."
          )
        elif new_id in teachers_df[id_col].astype(str).values:
          st.warning("هذا الرقم القومي مسجل مسبقاً.")
        else:
          new_t_df = pd.DataFrame(
              [{
                  "Code": new_code,
                  "Name": new_name,
                  "National_ID": new_id,
                  "Program": new_prog,
                  "School": new_school,
                  "Administration": new_admin,
                  "Phone": new_phone,
                  "Job_Title": new_job,
              }]
          )
          teachers_df = pd.concat([teachers_df, new_t_df], ignore_index=True)
          teachers_df.to_csv(TEACHERS_FILE, index=False, encoding="utf-8-sig")
          st.success(f"تمت إضافة المعلم {new_name} بنجاح!")
          st.rerun()

  st.subheader("قائمة المعلمين المسجلين:")
  st.dataframe(teachers_df, use_container_width=True)

# 3. صفحة سجل الحضور والتقارير (مع ضبط ارتفاع الصفوف هندسياً لتندمج الـ 19 صفاً مع التواقيع في صفحة A4 واحدة تماماً)
elif choice == "سجل الحضور والتقارير":
  st.header("📋 سجل الحضور والتقارير اليومية")

  if log_df.empty or log_df["National_ID"].dropna().empty:
    st.info("لا توجد سجلات حضور حتى الآن.")
  else:
    col1, col2 = st.columns(2)
    with col1:
      filter_date = st.date_input("تصفية حسب التاريخ", datetime.now())

    filtered_log = log_df[log_df["Date"] == str(filter_date)]

    st.metric(
        label="إجمالي الحضور في هذا التاريخ", value=len(filtered_log)
    )
    st.dataframe(filtered_log, use_container_width=True)

    csv_data = filtered_log.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 تحميل السجل كملف CSV",
        data=csv_data,
        file_name=f"attendance_giza_{filter_date}.csv",
        mime="text/css",
    )

    st.markdown("---")
    st.subheader("🖨️ طباعة كشف إثبات الحضور الرسمي (مطابق للصورة)")

    # توليد صفوف الجدول الرسمية (بارتفاع 11.5mm لكل صف لضمان احتواء الـ 19 صفاً والتواقيع تماماً)
    rows_html = ""
    for idx in range(1, 20):
      if idx <= len(filtered_log):
        r = filtered_log.iloc[idx - 1]
        r_name = r.get("Name", "")
        r_code = r.get("Teacher_Code", r.get("Code_ID", ""))
        r_id = r.get("National_ID", "")
        r_prog = r.get("Program", "")
        r_datetime = f"{r.get('Date', '')} | {r.get('Time', '')}"
        r_serial = r.get("Code_ID", f"A-{idx:03d}")
        rows_html += f"""
                <tr style="height: 11.5mm;">
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;">{idx}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px; font-weight: bold;">{r_serial}</td>
                    <td style="border: 1px solid #444; padding: 1px 3px; text-align: right; font-size: 11px;">{r_name}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;">{r_code}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;">{r_id}</td>
                    <td style="border: 1px solid #444; padding: 1px 3px; text-align: right; font-size: 11px;">{r_prog}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 10px;">{r_datetime}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center;"></td>
                </tr>
                """
      else:
        rows_html += f"""
                <tr style="height: 11.5mm;">
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;">{idx}</td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px 3px; text-align: right; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px 3px; text-align: right; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center; font-size: 11px;"></td>
                    <td style="border: 1px solid #444; padding: 1px; text-align: center;"></td>
                </tr>
                """

    official_report_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>كشف إثبات حضور المعلمين - {filter_date}</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 0mm;
        }}
        html, body {{
            width: 297mm;
            height: 210mm;
            margin: 0;
            padding: 0;
            font-family: 'Tahoma', 'Arial', sans-serif;
            background: #fff;
            color: #000;
            box-sizing: border-box;
            overflow: hidden;
        }}
        .sheet {{
            width: 289mm;
            height: 202mm;
            margin: 4mm auto;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 2px;
        }}
        .title {{
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            color: #0b2246;
            margin-bottom: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }}
        th {{
            background-color: #0b2246;
            color: white;
            border: 1px solid #0b2246;
            padding: 3px 2px;
            font-size: 11px;
            text-align: center;
        }}
        .signatures {{
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
            margin-bottom: 2px;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
        }}
        .footer {{
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            border-top: 1px solid #ccc;
            padding-top: 2px;
        }}
        .print-btn {{
            display: block;
            width: 200px;
            margin: 10px auto;
            background: #0b2246;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ background: white; margin: 0; }}
            .sheet {{ width: 100%; height: 100vh; margin: 0; padding: 4mm; }}
        }}
    </style>
</head>
<body>
    <div class="sheet">
        <div>
            <div class="header-top">
                <div>التاريخ: {filter_date}</div>
                <div>الأكاديمية المهنية للمعلمين - فرع الجيزة</div>
            </div>
            
            <div class="title">كشف إثبات حضور المعلمين ({filter_date})</div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 4%;">م</th>
                        <th style="width: 7%;">الترتيب</th>
                        <th style="width: 22%;">الاسم</th>
                        <th style="width: 9%;">كود المعلم</th>
                        <th style="width: 14%;">الرقم القومي</th>
                        <th style="width: 17%;">البرنامج</th>
                        <th style="width: 14%;">وقت وتاريخ الوصول</th>
                        <th style="width: 13%;">التوقيع</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        
        <div>
            <div class="signatures">
                <div>المختص<br><br>........................</div>
                <div>مسئول المعمل<br><br>........................</div>
                <div>مدير إدارة الفرع<br><br>........................</div>
            </div>
            
            <div class="footer">
                <div>الأكاديمية المهنية للمعلمين - فرع الجيزة | كشف حضور اليوم</div>
                <div>صفحة 1 من 1</div>
            </div>
        </div>
        
        <button class="print-btn" onclick="window.print()">🖨️ طباعة الكشف الرسمي</button>
    </div>
</body>
</html>"""

    report_popup_btn = f"""
        <script>
        function openReportWindow() {{
            var htmlContent = {repr(official_report_html)};
            var win = window.open('', '_blank', 'width=950,height=800,scrollbars=yes');
            win.document.write(htmlContent);
            win.document.close();
        }}
        </script>
        <button onclick="openReportWindow()" style="width: 100%; background-color: #0b2246; color: white; padding: 14px 20px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; font-family: 'Tahoma', sans-serif;">
            🖨️ فتح وعرض كشف الحضور الرسمي للطباعة (صفحة A4 واحدة متكاملة نهائية)
        </button>
        """
    components.html(report_popup_btn, height=70)
