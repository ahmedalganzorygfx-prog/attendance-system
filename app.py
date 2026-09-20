import base64
import os
from datetime import datetime
import pandas as pd
import streamlit as st

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title="نظام الحضور - الأكاديمية المهنية للمعلمين بالجيزة",
    page_icon="📊",
    layout="wide",
)

# تنسيقات الواجهة وتوسيط العنوان واتجاه RTL وإخفاء عناصر الموقع عند الطباعة المباشرة
st.markdown(
    """
    <style>
    h1, h2, h3 {
        text-align: center;
    }
    .stApp {
        direction: rtl;
        text-align: right;
    }
    .stSidebar {
        direction: rtl;
        text-align: right;
    }
    
    /* عند الطباعة، نقوم بإخفاء كل شي في الموقع ما عدا صندوق التذكرة فقط */
    @media print {
        body * {
            visibility: hidden !important;
        }
        #printable-ticket-box, #printable-ticket-box * {
            visibility: visible !important;
        }
        #printable-ticket-box {
            position: fixed !important;
            left: 50% !important;
            top: 50% !important;
            transform: translate(-50%, -50%) !important;
            width: 10cm !important;
            height: 14cm !important;
            padding: 20px !important;
            background: white !important;
            border: 2px solid #10233F !important;
            z-index: 999999 !important;
        }
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

# العنوان الرئيسي للتطبيق
st.title("🏛️ نظام تسجيل ومتابعة الحضور")
st.subheader("فرع الأكاديمية المهنية للمعلمين بالجيزة")
st.markdown("---")

# القائمة الجانبية للتنقل بين الصفحات
menu = ["تسجيل الحضور", "إدارة المعلمين", "سجل الحضور والتقارير"]
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

# 1. صفحة تسجيل الحضور
if choice == "تسجيل الحضور":
  st.header("📝 تسجيل حضور المعلمين وإصدار التذكرة")

  nat_id = st.text_input(
      "أدخل الرقم القومي (14 رقم):", max_chars=14, key="nat_id_input"
  )

  if st.button("تسجيل الحضور وإصدار التذكرة", type="primary"):
    if len(nat_id) != 14 or not nat_id.isdigit():
      st.error("الرجاء إدخال رقم قومي صحيح مكون من 14 رقماً.")
    else:
      id_col = (
          "National_ID"
          if "National_ID" in teachers_df.columns
          else teachers_df.columns[2]
      )
      name_col = (
          "Name" if "Name" in teachers_df.columns else teachers_df.columns[1]
      )
      program_col = (
          "Program"
          if "Program" in teachers_df.columns
          else teachers_df.columns[3]
      )
      code_col = (
          "Code" if "Code" in teachers_df.columns else teachers_df.columns[0]
      )

      teacher = teachers_df[teachers_df[id_col].astype(str).str.strip() == nat_id]

      if teacher.empty:
        st.warning(
            "هذا الرقم القومي غير مسجل في قاعدة البيانات. يرجى إضافته من صفحة"
            " 'إدارة المعلمين'."
        )
      else:
        name = teacher.iloc[0][name_col]
        program = (
            teacher.iloc[0][program_col]
            if program_col in teacher.columns
            else "تطبيقات تربوية للمعلم المساعد"
        )
        t_code = (
            teacher.iloc[0][code_col]
            if code_col in teacher.columns
            else "367966"
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%I:%M:%S %p")

        already_logged = log_df[
            (log_df["National_ID"].astype(str).str.strip() == nat_id)
            & (log_df["Date"] == current_date)
        ]

        if not already_logged.empty:
          serial_no = already_logged.iloc[0].get("Code_ID", "A-001")
          st.info(f"المعلم/ـة **{name}** مسجل بالفعل لهذا اليوم.")
          st.session_state["ticket_data"] = {
              "name": name,
              "program": program,
              "id": nat_id,
              "code": t_code,
              "serial": serial_no,
              "datetime": f"{current_date} | {already_logged.iloc[0]['Time']}",
          }
        else:
          today_logs = log_df[log_df["Date"] == current_date]
          serial_num = len(today_logs) + 1
          serial_str = f"A-{serial_num:03d}"

          new_entry = pd.DataFrame(
              [{
                  "National_ID": nat_id,
                  "Name": name,
                  "School": "فرع الجيزة",
                  "Program": program,
                  "Code_ID": serial_str,
                  "Date": current_date,
                  "Time": current_time,
                  "Status": "حاضر",
              }]
          )
          log_df = pd.concat([log_df, new_entry], ignore_index=True)
          log_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

          st.success(
              f"تم تسجيل الحضور وإصدار التذكرة بنجاح برقم الأسبقية:"
              f" **{serial_str}**"
          )
          st.session_state["ticket_data"] = {
              "name": name,
              "program": program,
              "id": nat_id,
              "code": t_code,
              "serial": serial_str,
              "datetime": f"{current_date} | {current_time}",
          }

  # عرض التذكرة وتوفير زر طباعة مباشر وزر تحميل ملف تذكرة مستقل
  if "ticket_data" in st.session_state:
    t = st.session_state["ticket_data"]
    st.markdown("---")

    # صندوق المعاينة الخاص بالتذكرة
    ticket_html_visual = f"""
        <div id="printable-ticket-box" style="border: 2px solid #10233F; padding: 25px; border-radius: 10px; background-color: #ffffff; max-width: 450px; margin: auto; font-family: 'Cairo', sans-serif;">
            <div style="text-align: center; color: #10233F; font-weight: bold; font-size: 18px;">الأكاديمية المهنية للمعلمين</div>
            <div style="text-align: center; color: #555; font-size: 14px; margin-bottom: 5px;">فرع الجيزة</div>
            <hr style="border: 0.5px solid #10233F;">
            <div style="text-align: center; font-size: 12px; color: #666;">تذكرة أسبقية الحضور</div>
            
            <div style="text-align: center; background-color: #fdf8e2; border: 1.5px dashed #C9A227; padding: 10px; border-radius: 8px; margin: 15px 0;">
                <span style="font-size: 26px; font-weight: bold; color: #d9534f;">[ {t['serial']} ]</span>
            </div>
            
            <div style="font-size: 14px; line-height: 2; color: #222; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; padding: 10px 0; margin-bottom: 15px;">
                <b>الاسم:</b> {t['name']}<br>
                <b>البرنامج:</b> {t['program']}<br>
                <b>الرقم القومي:</b> {t['id']}<br>
                <b>كود المعلم:</b> {t['code']}<br>
                <b>الوقت والتاريخ:</b> {t['datetime']}
            </div>
            
            <div style="border: 1px solid #e0a800; background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-size: 12px; margin-bottom: 15px;">
                <b>⚠️ تنبيه هام ومستندات مطلوبة:</b><br>
                • يرجى تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.<br>
                • صورة بطاقة الرقم القومي سارية.<br>
                • إيصال الدفع إن وجد.
            </div>
            
            <div style="text-align: center; font-size: 13px; color: #10233F; font-weight: bold;">
                أهلاً بكم في فرع الجيزة - يرجى الانتظار لحين استدعائكم
            </div>
        </div>
        """
    st.markdown(ticket_html_visual, unsafe_allow_html=True)

    # إنشاء ملف HTML مستقل وقابل للتنزيل الفوري
    standalone_html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تذكرة الحضور - {t['serial']}</title>
            <style>
                body {{
                    font-family: 'Cairo', Tahoma, sans-serif;
                    background: #fff;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .ticket-box {{
                    width: 10cm;
                    padding: 20px;
                    border: 2px solid #10233F;
                    border-radius: 10px;
                    background-color: #ffffff;
                }}
            </style>
        </head>
        <body onload="window.print();">
            <div style="border: 2px solid #10233F; padding: 25px; border-radius: 10px; width: 10cm; background-color: #ffffff; font-family: 'Cairo', sans-serif;">
                <div style="text-align: center; color: #10233F; font-weight: bold; font-size: 18px;">الأكاديمية المهنية للمعلمين</div>
                <div style="text-align: center; color: #555; font-size: 14px; margin-bottom: 5px;">فرع الجيزة</div>
                <hr style="border: 0.5px solid #10233F;">
                <div style="text-align: center; font-size: 12px; color: #666;">تذكرة أسبقية الحضور</div>
                
                <div style="text-align: center; background-color: #fdf8e2; border: 1.5px dashed #C9A227; padding: 10px; border-radius: 8px; margin: 15px 0;">
                    <span style="font-size: 26px; font-weight: bold; color: #d9534f;">[ {t['serial']} ]</span>
                </div>
                
                <div style="font-size: 14px; line-height: 2; color: #222; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; padding: 10px 0; margin-bottom: 15px;">
                    <b>الاسم:</b> {t['name']}<br>
                    <b>البرنامج:</b> {t['program']}<br>
                    <b>الرقم القومي:</b> {t['id']}<br>
                    <b>كود المعلم:</b> {t['code']}<br>
                    <b>الوقت والتاريخ:</b> {t['datetime']}
                </div>
                
                <div style="border: 1px solid #e0a800; background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-size: 12px; margin-bottom: 15px;">
                    <b>⚠️ تنبيه هام ومستندات مطلوبة:</b><br>
                    • تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.<br>
                    • صورة بطاقة الرقم القومي سارية.<br>
                    • إيصال الدفع إن وجد.
                </div>
                
                <div style="text-align: center; font-size: 13px; color: #10233F; font-weight: bold;">
                    أهلاً بكم في فرع الجيزة - يرجى الانتظار لحين استدعائكم
                </div>
            </div>
        </body>
        </html>
        """

    b64_data = base64.b64encode(standalone_html.encode("utf-8")).decode("utf-8")
    download_link = f'<a href="data:text/html;base64,{b64_data}" download="ticket_{t["serial"]}.html" style="text-decoration: none;"><button style="background-color: #28a745; color: white; padding: 12px 20px; border: none; border-radius: 5px; font-size: 15px; font-weight: bold; cursor: pointer; width: 100%;">📥 تحميل ملف التذكرة (جاهز للطباعة)</button></a>'

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
      if st.button("إغلاق التذكرة"):
        if "ticket_data" in st.session_state:
          del st.session_state["ticket_data"]
        st.rerun()
    with c2:
      # زر طباعة مباشر يعتمد على تنسيق CSS المخفي
      st.markdown(
          """
            <button onclick="window.print()" style="background-color: #ff4b4b; color: white; padding: 12px 20px; border: none; border-radius: 5px; font-size: 15px; font-weight: bold; cursor: pointer; width: 100%;">🖨️ طباعة التذكرة مباشرة</button>
            """,
          unsafe_allow_html=True,
      )
    with c3:
      st.markdown(download_link, unsafe_allow_html=True)

# 2. صفحة إدارة المعلمين
elif choice == "إدارة المعلمين":
  st.header("👥 قاعدة بيانات المعلمين")

  with st.expander("➕ إضافة معلم جديد"):
    with st.form("add_teacher_form"):
      new_id = st.text_input("الرقم القومي (14 رقم)", max_chars=14)
      new_name = st.text_input("الاسم الكامل")
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
                  "Code": str(int(teachers_df.shape[0]) + 367900),
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

# 3. صفحة سجل الحضور والتقارير
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
        mime="text/csv",
    )
