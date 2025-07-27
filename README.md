<<<<<<< HEAD
# Instagram Automation Dashboard

A full-stack web application for managing Instagram automation scripts with React frontend and Flask backend.

## Features

### 🏠 Dashboard
- Real-time monitoring of all automation scripts
- Status tracking and activity logs
- Centralized control panel

### 📸 Instagram Daily Post
- Upload images or videos to multiple accounts simultaneously
- Support for up to 10 accounts
- Auto-caption generation
- Concurrent posting with progress monitoring

### 💬 Instagram DM Automation
- AI-powered personalized messaging
- Bulk DM campaigns across multiple accounts
- Response tracking and analysis
- Rate limiting protection

### 🔥 Instagram Account Warmup
- Human-like behavior simulation
- Multiple activity types (scrolling, liking, watching)
- Configurable duration and timing
- Concurrent account processing

## Tech Stack

### Frontend
- React 18 with TypeScript
- React Router for navigation
- Axios for API communication
- Modern CSS with responsive design

### Backend
- Flask with CORS support
- File upload handling
- Real-time logging system
- Thread-based script execution

## Installation

### Prerequisites
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- pip package manager

### Frontend Setup
```bash
cd frontend
npm install
npm start
```
The frontend will run on http://localhost:3000

### Backend Setup
```bash
cd backend
pip install Flask Flask-CORS Werkzeug python-dotenv openpyxl playwright
python app.py
```
The backend will run on http://localhost:5000

## Usage

1. **Start the Backend**: Run the Flask server
2. **Start the Frontend**: Run the React development server
3. **Access Dashboard**: Open http://localhost:3000
4. **Select Script**: Click on any of the 3 automation buttons
5. **Configure**: Fill in the required settings and upload files
6. **Monitor**: Watch real-time logs and progress

## File Requirements

### Daily Post Script
- **Accounts File**: Excel/CSV with Username and Password columns
- **Media File**: Images (.jpg, .png, .gif) or Videos (.mp4, .mov, .avi)

### DM Automation Script
- **Bot Accounts File**: Excel/CSV with Instagram account credentials
- **Target Accounts File**: Excel/CSV with target user information (optional)
- **Prompt File**: Text file with DM template (optional)

### Account Warmup Script
- **Accounts File**: Excel/CSV with Username and Password columns

## API Endpoints

### General
- `GET /api/health` - Health check
- `GET /api/scripts` - List all scripts
- `GET /api/script/{id}/status` - Get script status
- `GET /api/script/{id}/logs` - Get script logs
- `POST /api/script/{id}/stop` - Stop script

### Script-Specific
- `POST /api/daily-post/start` - Start daily post automation
- `POST /api/dm-automation/start` - Start DM automation
- `POST /api/warmup/start` - Start account warmup

## Configuration

### Environment Variables
- `DEEPSEEK_API_KEY` - API key for AI message generation (optional)

### Upload Limits
- Max file size: 50MB
- Supported formats: Excel, CSV, JPG, PNG, MP4, MOV, AVI, etc.

## Security Features

- File type validation
- Secure filename handling
- CORS configuration
- Input sanitization

## Development

### Project Structure
```
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # React components
│   │   └── App.tsx          # Main application
│   └── public/              # Static assets
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── uploads/            # Uploaded files
│   └── logs/               # Script logs
└── README.md               # This file
```

### Adding New Scripts
1. Create API endpoint in `backend/app.py`
2. Add React component in `frontend/src/components/`
3. Update routing in `App.tsx`
4. Add button to `HomePage.tsx`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and personal use. Please respect Instagram's Terms of Service when using automation tools.

## Support

For issues and questions:
1. Check the real-time logs in the application
2. Review the console output
3. Verify file formats and requirements
4. Ensure proper API configuration
=======
# instaAutomation
>>>>>>> 633d021ef513f613f9a52c3bc094c39a8cec434e
