@echo off
echo Starting fresh Git setup...

REM Navigate to project directory
cd /d "c:\Users\PC\Desktop\instaUI2"

REM Remove existing git
rmdir /s /q .git

REM Initialize new git repository
git init

REM Add all files
git add .

REM Initial commit
git commit -m "Initial commit - Instagram automation project"

REM Rename branch to main
git branch -M main

REM Add remote origin
git remote add origin https://github.com/AbdullahYounas0/InstaAutomation.git

REM Force push to overwrite remote
git push -f origin main

echo Git setup completed!
pause
