@echo off
echo ================================================
echo     ZETOM — FULL PROJECT MOVE AWAY FROM ONEDRIVE
echo ================================================

REM === 1. Create new safe directory ===
set NEW_PATH=C:\Projects\zetom

echo Creating directory %NEW_PATH%...
mkdir %NEW_PATH%

echo Copying project from OneDrive to %NEW_PATH%...
xcopy "C:\Users\tymir\OneDrive\Documents\zetom" "%NEW_PATH%" /E /H /C /Y

echo Done copying.
echo.

REM === 2. Remove old venv ===
echo Removing old virtual environment...
rmdir /S /Q "%NEW_PATH%\.venv"

REM === 3. Create new virtual environment ===
echo Creating new virtual environment...
cd /D %NEW_PATH%
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate

REM === 4. Install dependencies ===
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM === 5. Remove old SQLite DB if exists ===
echo Removing old database...
if exist db.sqlite3 del db.sqlite3

REM === 6. Apply migrations ===
echo Applying migrations...
python manage.py migrate

REM === 7. Collect static files ===
echo Collecting static files...
python manage.py collectstatic --clear --noinput

REM === 8. Start server ===
echo Starting Django development server...
python manage.py runserver

pause
