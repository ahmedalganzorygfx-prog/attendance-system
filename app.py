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

# كود CSS لتوسيط العنوان وضبط الاتجاه من اليمين لليسار (RTL)
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


# وظائف لإنشاء ملفات افتراضية إذا لم تكن موجودة
def init_files():
  if not os.path.exists(TEACHERS_FILE):
    df_default = pd.DataFrame(
        columns=[
            "National_ID",
            "Name",
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


# تحميل البيانات مع معالجة الترميز والأعمدة الناقصة تلقائياً
@st.cache_data(ttl=2)
def load_data():
  try:
    teachers_df = pd.read_csv(TEACHERS_FILE, dtype=str, encoding="utf-8-sig")
  except:
    teachers_df = pd.read_csv(TEACHERS_FILE, dtype=str, encoding="latin1")

  try:
    log_df = pd.read_csv(LOG_FILE, dtype=str, encoding="utf-8-sig")
  except:
    log_df = pd.read_csv(LOG_FILE, dtype=str, encoding="latin1")

  # التأكد من وجود الأعمدة الأساسية لتعادي أي خطأ في الملفات القديمة
  expected_teacher_cols = [
      "National_ID",
      "Name",
      "School",
      "Administration",
      "Phone",
      "Job_Title",
  ]
  for col in expected_teacher_cols:
    if col not in teachers_df.columns:
      teachers_df[col] = ""

  expected_log_cols = [
      "National_ID",
      "Name",
      "School",
      "Date",
      "Time",
      "Status",
  ]
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
      # البحث عن المعلم
      teacher = teachers_df[teachers_df["National_ID"] == nat_id]
      if teacher.empty:
        st.warning(
            "هذا الرقم القومي غير مسجل في قاعدة البيانات. يرجى إضافته من صفحة"
            " 'إدارة المعلمين'."
        )
      else:
        name = teacher.iloc[0]["Name"]
        school = teacher.iloc[0]["School"]

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        # التحقق مما إذا تم تسجيل الحضور مسبقاً اليوم
        already_logged = log_df[
            (log_df["National_ID"] == nat_id)
            & (log_df["Date"] == current_date)
        ]

        if not already_logged.empty:
          st.info(f"المعلم/ـة **{name}** مسجل بالفعل لهذا اليوم.")
        else:
          new_entry = pd.DataFrame(
              [{
                  "National_ID": nat_id,
                  "Name": name,
                  "School": school,
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
        if len(new_id) != 14 or not new_id.isdigit() or not new_name:
          st.error(
              "الرجاء التأكد من صحة الرقم القومي (14 رقماً) وإدخال الاسم على"
              " الأقل."
          )
        elif new_id in teachers_df["National_ID"].values:
          st.warning("هذا الرقم القومي مسجل مسبقاً.")
        else:
          new_t_df = pd.DataFrame(
              [{
                  "National_ID": new_id,
                  "Name": new_name,
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

    # زر لتنزيل السجل بصيغة CSV
    csv_data = filtered_log.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 تحميل السجل كملف CSV",
        data=csv_data,
        file_name=f"attendance_giza_{filter_date}.csv",
        mime="text/csv",
    )
