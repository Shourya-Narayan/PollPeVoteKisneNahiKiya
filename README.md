# ME 104 Poll Attendance & Absentee Tracker

An automated tool built specifically for **Mechanical Workshop [ME 104] (60 Students)** to process WhatsApp poll screenshots, map real-world WhatsApp nicknames/aliases to official roll numbers, and compute missing/absent students automatically.

---

## 📁 Project Structure

```
attendance_checker/
├── students.py           # Official 60-student batch roster & pre-trained WhatsApp alias database
├── matcher.py            # Cleans OCR noise, matches names using alias dictionary + fuzzy matching
├── ocr.py                # Fast, completely offline OCR engine using Windows Native OCR
├── cli.py                # Command Line Tool (direct image inputs)
├── app.py                # Streamlit Web App (drag-and-drop screenshots)
├── run_app.bat           # 1-click launcher for the Streamlit Web App
└── README.md             # Instructions
```

---

## 🚀 How to Use

### Option 1: Web App (Drag & Drop UI)
1. Double-click **`run_app.bat`** (or run `python -m streamlit run app.py`).
2. Your browser will open the app automatically.
3. Drag and drop your poll screenshots.
4. Click **"Process Screenshots"**.
5. Instantly view:
   - **Remaining / Absent Students** table.
   - **Ready-to-copy WhatsApp reminder message**.
   - **Downloadable CSV report**.

### Option 2: Command Line (CLI)
Run `cli.py` passing image file paths or an entire folder:

```bash
# Pass image paths directly:
python cli.py screenshot1.jpg screenshot2.jpg screenshot3.jpg

# Or point to a folder containing screenshots:
python cli.py --folder "C:\path\to\screenshots"
```

---

## ⚡ Key Features
- **100% Offline & Free:** Uses Windows built-in Native OCR (no Tesseract installation or cloud API keys required).
- **Smart Alias Resolution:** Recognizes handles like `_exe.ra.ja` -> Raja S Sornendra, `Shubham Karnataka` -> Shubham Rathod, `You Are Important` -> Harsh Raj, `You` -> Shourya Narayan, etc.
- **Accurate Subtraction:** Computes `Master 60 − Voted List = Remaining Students` in less than 2 seconds.
