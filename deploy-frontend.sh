#!/bin/bash

# Build the frontend with updated API URLs
echo "Building frontend with production URLs..."
cd frontend
npm run build

echo "Frontend build completed!"
echo ""
echo "Next steps:"
echo "1. Upload the contents of frontend/build/ to your VPS web directory"
echo "2. Make sure your backend is running on your VPS and accessible via https://wdyautomation.shop/api"
echo "3. Ensure your nginx configuration is properly set up to serve the frontend and proxy API requests"
echo ""
echo "The API URLs have been updated from localhost:5000 to wdyautomation.shop"
