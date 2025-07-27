# Build the frontend with updated API URLs
Write-Host "Building frontend with production URLs..." -ForegroundColor Green
Set-Location frontend
npm run build

Write-Host "Frontend build completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Upload the contents of frontend/build/ to your VPS web directory"
Write-Host "2. Make sure your backend is running on your VPS and accessible via https://wdyautomation.shop/api"
Write-Host "3. Ensure your nginx configuration is properly set up to serve the frontend and proxy API requests"
Write-Host ""
Write-Host "The API URLs have been updated from localhost:5000 to wdyautomation.shop" -ForegroundColor Cyan
