# Excel Skills Assessment System

An AI-powered automated interview system for evaluating Excel proficiency using multi-agent architecture.

## Quick Start
### 1. Create a .env file 
- GROQ_API_KEY=your groq api key
- NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
### 2. Start the Backend
`
chmod +x start_backend.sh
./start_backend.sh
`

### 3. Start the Frontend (in a new terminal)
`
chmod +x start_frontend.sh
./start_frontend.sh
`

### 3. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs


## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check internet connection (required for Groq API calls)

### Frontend connection errors
- Verify backend is running on port 8000
- Ensure CORS is properly configured
- Check browser console for detailed error messages
