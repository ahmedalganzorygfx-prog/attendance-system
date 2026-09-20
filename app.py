import os
from datetime import datetime
import pandas as pd
import streamlit as st

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title=(
        "الأكاديمية المهنية للمعلمين - فرع الجيزة | نظام أسبقية الحضور"
    ),
    page_icon="🏛️",
    layout="centered",
)

# تنسيقات الواجهة العامة لتشبه التطبيق المكتبي تماماً
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
    @media print {
        body * {
            visibility: hidden;
        }
        #printable-ticket, #printable-ticket * {
            visibility: visible;
        }
        #printable-ticket {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            background: white;
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

  # إطار البحث (مطابق لتصميم الجهاز)
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

  # إطار بيانات المعلم المسجل (مطابق للصورة تماماً)
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

  # زر تأكيد الحضور الأخضر الكبير
  if st.button(
      "تأكيد الحضور وإصدار التذكرة النهائية",
      type="primary",
      use_container_width=True,
  ):
    if "current_selected_teacher" in st.session_state:
      ft = st.session_state["current_selected_teacher"]
      current_date = datetime.now().strftime("%Y-%m-%d")
      current_time = datetime.now().strftime("%I:%M:%S %p")

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
            "code": ft["code"],
            "serial": serial_str,
            "datetime": f"{current_date} | {current_time}",
        }
    else:
      st.warning("الرجاء البحث عن المعلم أولاً قبل تأكيد الحضور.")

  # عرض التذكرة بشكل نظيف ومستقل تماماً
  if "show_ticket_modal" in st.session_state:
    tk = st.session_state["show_ticket_modal"]
    st.markdown("---")
    st.success("تم تسجيل الحضور وإصدار التذكرة بنجاح")

    with st.container():
      st.markdown(
          "<div id='printable-ticket' style='border: 2px solid #10233F;"
          " padding: 25px; border-radius: 8px; background-color: #ffffff;"
          " max-width: 450px; margin: auto;'>",
          unsafe_allow_html=True,
      )

      st.markdown(
          "<h3"
          " style='text-align: center; color: #10233F; margin-bottom: 0;'>الأكاديمية"
          " المهنية للمعلمين</h3>",
          unsafe_allow_html=True,
      )
      st.markdown(
          "<p"
          " style='text-align: center; color: #555; font-size: 14px;"
          " margin-top: 0;'>فرع الجيزة</p>",
          unsafe_allow_html=True,
      )
      st.markdown("---")
      st.markdown(
          "<p"
          " style='text-align: center; font-size: 13px; color:"
          " #666;'>تذكرة أسبقية الحضور</p>",
          unsafe_allow_html=True,
      )

      st.markdown(
          f"<div style='text-align: center; background-color: #fdf8e2; border:"
          " 1.5px dashed #C9A227; padding: 10px; border-radius: 8px; margin:"
          " 15px 0;'><span style='font-size: 26px; font-weight: bold; color:"
          f" #d9534f;'>[ {tk['serial']} ]</span></div>",
          unsafe_allow_html=True,
      )

      st.markdown(
          f"<div style='font-size: 15px; line-height: 2.2; color:"
          f" #222; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;"
          " padding: 10px 0;'>"
          f"<b>الاسم:</b> {tk['name']}<br>"
          f"<b>البرنامج:</b> {tk['program']}<br>"
          f"<b>الرقم القومي:</b> {tk['id']}<br>"
          f"<b>كود المعلم:</b> {tk['code']}<br>"
          f"<b>الوقت والتاريخ:</b> {tk['datetime']}"
          "</div>",
          unsafe_allow_html=True,
      )

      st.warning(
          "⚠️ تنبيه هام ومستندات مطلوبة:\n\n"
          "• يرجى تجهيز صحيفة أحوال إلكترونية حديثة معتمدة.\n"
          "• صورة بطاقة الرقم القومي سارية.\n"
          "• إيصال الدفع إن وجد."
      )

      st.markdown(
          "<p"
          " style='text-align: center; font-size: 13px; color: #10233F;"
          " font-weight: bold; margin-top: 15px;'>أهلاً بكم في فرع الجيزة - يرجى"
          " الانتظار لحين استدعائكم</p>",
          unsafe_allow_html=True,
      )

      st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
      if st.button("إغلاق", use_container_width=True):
        if "show_ticket_modal" in st.session_state:
          del st.session_state["show_ticket_modal"]
        if "current_selected_teacher" in st.session_state:
          del st.session_state["current_selected_teacher"]
        st.rerun()
    with b_col2:
      if st.button("عرض التذكرة بالكامل", type="secondary", use_container_width=True):
        st.info("التذكرة معروضة بالكامل بالأعلى وجاهزة للطباعة.")
    with b_col3:
      if st.button("طباعة التذكرة", type="primary", use_container_width=True):
        st.markdown(
            """
                <script>
                window.print();
                </script>
                """,
            unsafe_allow_html=True,
        )

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
        mime="text/css",
    )
