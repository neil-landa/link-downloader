@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Link Downloader server...
echo Open http://localhost:5000 in your browser
echo.
python app.py
pause

