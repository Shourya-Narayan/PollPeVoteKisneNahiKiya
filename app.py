import streamlit as st
import pandas as pd
import tempfile
import os
import platform
from students import MASTER_STUDENTS, KNOWN_ALIASES
from gemini_engine import analyze_screenshots_with_gemini

# Check OS for offline OCR availability
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    from ocr import extract_text_from_image
    from matcher import process_extracted_lines

st.set_page_config(
    page_title="Mechatronics Student Group Attendance and Vote Tracker",
    page_icon="🤖",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222A;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #333;
        text-align: center;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Mechatronics Student Group Attendance and Vote Tracker")
st.caption("Powered by **Gemini Multimodal Vision API** with automatic nickname mapping and absentee tracking.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Engine & API Settings")
    
    engine_options = ["Gemini AI (Vision API)"]
    if IS_WINDOWS:
        engine_options.append("Offline Native OCR (No API Key)")

    engine = st.radio(
        "Select Processing Engine:",
        options=engine_options,
        index=0,
        help="Gemini AI uses multimodal intelligence to directly identify batchmates from screenshots."
    )

    gemini_key = ""
    if engine == "Gemini AI (Vision API)":
        env_key = os.environ.get("GEMINI_API_KEY", "")
        # Also check Streamlit secrets if deployed on cloud
        if not env_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            env_key = st.secrets["GEMINI_API_KEY"]

        gemini_key = st.text_input(
            "🔑 Gemini API Key:",
            value=env_key,
            type="password",
            placeholder="AIzaSy...",
            help="Get your free key from Google AI Studio (aistudio.google.com)"
        )
        if not gemini_key:
            st.warning("⚠️ Please provide a Gemini API Key.")
            st.markdown("[👉 Get a free Gemini API Key](https://aistudio.google.com/app/apikey)")
        else:
            st.success("API Key detected!")

    st.divider()
    st.info(f"🎓 **Batch:** Mechanical Workshop [ME 104]\n\n👥 **Total Batch:** {len(MASTER_STUDENTS)} Students")
    
    with st.expander("📖 View Full Master List (60)"):
        df_master = pd.DataFrame([
            {"Roll No": r, "Name": n} for r, n in MASTER_STUDENTS.items()
        ])
        st.dataframe(df_master, hide_index=True, use_container_width=True)

# Main Upload Area
uploaded_files = st.file_uploader(
    "📤 Upload WhatsApp Poll Screenshots (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    can_proceed = True
    if engine == "Gemini AI (Vision API)" and not gemini_key.strip():
        can_proceed = False
        st.error("❌ Please enter your Gemini API Key in the left sidebar to use Gemini AI.")

    if can_proceed and st.button("🚀 Process Screenshots", type="primary", use_container_width=True):
        matched = {}
        remaining = []
        unmapped = []

        with st.spinner("Analyzing screenshots with Gemini Vision AI..."):
            if engine == "Gemini AI (Vision API)":
                st.toast(f"Analyzing {len(uploaded_files)} screenshot(s) with Gemini 2.5 Flash Vision...")
                image_bytes = [file.read() for file in uploaded_files]
                try:
                    matched, remaining, unmapped = analyze_screenshots_with_gemini(
                        image_bytes_list=image_bytes,
                        api_key=gemini_key.strip()
                    )
                except Exception as e:
                    st.error(f"Gemini API Error: {str(e)}")
                    st.stop()
            else:
                st.toast(f"Running Offline Windows OCR on {len(uploaded_files)} screenshot(s)...")
                all_raw_lines = []
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name
                    try:
                        lines = extract_text_from_image(tmp_path)
                        all_raw_lines.extend(lines)
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                matched, remaining, unmapped = process_extracted_lines(all_raw_lines)

        # Metrics Display
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total Batch Size", len(MASTER_STUDENTS))
        col2.metric("✅ Total Voted / Present", len(matched), delta=f"{len(matched)} / {len(MASTER_STUDENTS)}")
        col3.metric("❌ Remaining / Absent", len(remaining), delta=f"-{len(remaining)} pending", delta_color="inverse")

        st.divider()

        tab1, tab2, tab3 = st.tabs(["❌ Remaining Students", "✅ Voted Students", "🔍 Diagnostics & External Accounts"])

        with tab1:
            if remaining:
                st.error(f"⚠️ {len(remaining)} student(s) have NOT voted yet:")
                
                df_rem = pd.DataFrame(remaining)
                df_rem.index = range(1, len(df_rem) + 1)
                st.dataframe(df_rem, use_container_width=True)

                # WhatsApp Quick Copy Reminder
                whatsapp_text = "*⚠️ ME 104 Workshop Poll / Submission Reminder:*\n"
                whatsapp_text += "The following student(s) have not responded yet:\n\n"
                for i, s in enumerate(remaining, 1):
                    whatsapp_text += f"{i}. {s['roll']} - {s['name']}\n"
                whatsapp_text += "\nPlease submit/vote as soon as possible."

                st.subheader("📲 WhatsApp Reminder Message (Ready to Copy)")
                st.text_area("Copy and paste directly in group:", whatsapp_text, height=140)

                # Download CSV
                csv_rem = df_rem.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Absentee List (CSV)",
                    csv_rem,
                    "remaining_students.csv",
                    "text/csv"
                )
            else:
                st.balloons()
                st.success("🎉 All 60 students in the batch have voted! No absentees.")

        with tab2:
            st.subheader(f"List of Students Who Voted ({len(matched)})")
            if matched:
                df_voted = pd.DataFrame(list(matched.values()))
                df_voted = df_voted.sort_values(by="roll")
                df_voted.index = range(1, len(df_voted) + 1)
                df_voted = df_voted.rename(columns={
                    "roll": "Roll No",
                    "name": "Official Name",
                    "raw_text": "Matched From (Poll Text)",
                    "match_type": "Engine"
                })
                
                search_query = st.text_input("🔍 Search Voted Students (Roll or Name):")
                if search_query:
                    filtered_df = df_voted[
                        df_voted["Official Name"].str.contains(search_query, case=False, na=False) |
                        df_voted["Roll No"].astype(str).str.contains(search_query)
                    ]
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.dataframe(df_voted, use_container_width=True)

                csv_voted = df_voted.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Voted List (CSV)",
                    csv_voted,
                    "voted_students.csv",
                    "text/csv"
                )

        with tab3:
            st.subheader("Diagnostics & External / Unrecognized Entries")
            if unmapped:
                st.warning(f"Detected {len(unmapped)} external or non-batch account(s):")
                st.code("\n".join(set(unmapped)))
            else:
                st.info("No unrecognized entries detected.")

else:
    st.info("👆 Please upload one or more poll screenshots to get started.")
