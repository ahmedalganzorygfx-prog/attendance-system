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

# تنسيقات الواجهة وتوسيط العنوان واتجاه RTL
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
    </style>
    """,
    unsafe_allow_html=True,
)

# أسماء ملفات البيانات
TEACHERS_FILE = "teachers_database.csv"
LOG_FILE = "attendance_log_giza.csv"


# وظائف لإنشاء ملفات افتراضية صحيحة إذا لم تكن موجودة أو كانت تالفة
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


# تحميل البيانات مع ضبط الفاصل (;) ومعالجة الأعمدة الناقصة تلقائياً
@st.cache_data(ttl=2)
def load_data():
  # قراءة ملف المعلمين
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

  # قراءة ملف السجلات مع التأكد من سلامة الأعمدة
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
  st.header("📝 تسجيل حضور المعلمين")

  nat_id = st.text_input(
      "أدخل الرقم القومي (14 رقم):", max_chars=14, key="nat_id_input"
  )

  if st.button("تسجيل الحضور", type="primary"):
    if len(nat_id) != 14 or not nat_id.isdigit():
      st.error("الرجاء إدخال رقم قومي صحيح مكون من 14 رقماً.")
    else:
      # تحديد أسماء الأعمدة بمرونة
      id_col = (
          "National_ID"
          if "National_ID" in teachers_df.columns
          else teachers_df.columns[2]
      )
      name_col = (
          "Name" if "Name" in teachers_df.columns else teachers_df.columns[1]
      )
      school_col = (
          "School"
          if "School" in teachers_df.columns
          else teachers_df.columns[-1]
      )

      teacher = teachers_df[teachers_df[id_col].astype(str).str.strip() == nat_id]

      if teacher.empty:
        st.warning(
            "هذا الرقم القومي غير مسجل في قاعدة البيانات. يرجى إضافته من صفحة"
            " 'إدارة المعلمين'."
        )
      else:
        name = teacher.iloc[0][name_col]
        school = (
            teacher.iloc[0][school_col]
            if school_col in teacher.columns
            else "غير متوفر"
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        already_logged = log_df[
            (log_df["National_ID"].astype(str).str.strip() == nat_id)
            & (log_df["Date"] == current_date)
        ]

        if not already_logged.empty:
          st.info(f"المعلم/ـة **{name}** مسجل بالفعل لهذا اليوم.")
        else:
          new_entry = pd.DataFrame(
              [{
                  "National_ID": nat_id,
                  "Name": name,
                  "School": str(school),
                  "Date": current_date,
                  "Time": current_time,
                  "Status": "حاضر",
              }]
          )
          log_df = pd.concat([log_df, new_entry], ignore_index=True)
          log_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
          st.success(
              f"تم تسجيل حضور المعلم/ـة: **{name}** بنجاح في تمام الساعة"
              f" {current_time}"
          )

# 2. صفحة إدارة المعلمين
elif choice == "إدارة المعلمين":
  st.header("👥 قاعدة بيانات المعلمين")

  with st.expander("➕ إضافة معلم جديد"):
    with st.form("add_teacher_form"):
      new_id = st.text_input("الرقم القومي (14 رقم)", max_chars=14)
      new_name = st.text_input("الاسم الكامل")
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
                  "Code": str(len(teachers_df) + 1),
                  "Name": new_name,
                  "National_ID": new_id,
                  "Program": "عام",
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
