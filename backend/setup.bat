@echo off
echo Setting up Instagram Daily Post Backend...
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installing Playwright browsers...
python -m playwright install chromium

echo.
echo Setup completed successfully!
echo You can now run the backend with: python app.py
pause
