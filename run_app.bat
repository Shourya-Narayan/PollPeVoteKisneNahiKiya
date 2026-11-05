@echo off
echo Starting ME 104 Attendance Tracker Web App...
cd /d "%~dp0"
python -m streamlit run app.py
pause
