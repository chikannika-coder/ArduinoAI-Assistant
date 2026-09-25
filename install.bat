@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info[0]==3 else 1)" >nul 2>nul && set "PY=python"
if not defined PY python3 -c "import sys" >nul 2>nul && set "PY=python3"
if not defined PY (
  echo.
  echo ไม่พบ Python 3 ในเครื่องนี้ ^(เครื่องนี้อาจมีแต่ Python 2 รุ่นเก่า^)
  echo ติดตั้ง Python 3 จาก https://www.python.org/downloads/
  echo ตอนติดตั้งให้ติ๊ก "Add python.exe to PATH" แล้วเปิดไฟล์นี้ใหม่
  echo.
  pause
  exit /b 1
)
echo ใช้ Python:
%PY% --version
echo กำลังติดตั้งโปรแกรมที่จำเป็น...
%PY% -m pip install -r requirements.txt
echo.
echo เสร็จแล้ว ดับเบิลคลิก run.bat เพื่อเปิดโปรแกรม
pause
