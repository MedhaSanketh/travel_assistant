# 🚀 Local Setup Guide - AI Travel Agent

## 📋 Prerequisites
- **Python 3.8+** installed on your system
- **VS Code** (or any Python IDE)
- **Git** (optional, for version control)

## 🔧 Step-by-Step Setup

### 1. Extract and Navigate to Your Project
```bash
# Extract the downloaded zip file
# Navigate to the project folder
cd your-travel-agent-folder
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv travel_agent_env
travel_agent_env\Scripts\activate

# macOS/Linux
python3 -m venv travel_agent_env
source travel_agent_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install streamlit==1.28.0
pip install python-dotenv==1.0.0
pip install crewai==0.28.0
pip install amadeus==8.0.0
pip install requests==2.31.0
pip install tabulate==0.9.0
```

**Or install all at once:**
```bash
pip install streamlit python-dotenv crewai amadeus requests tabulate
```

### 4. Set Up Environment Variables
1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` file with your actual API keys:
   ```
   GROQ_API_KEY=gsk_your_actual_groq_key_here
   AMADEUS_CLIENT_ID=your_actual_amadeus_client_id
   AMADEUS_CLIENT_SECRET=your_actual_amadeus_secret
   AMADEUS_ENV=test
   DEFAULT_CURRENCY=USD
   GOOGLE_PLACES_API_KEY=your_actual_google_places_key
   ```

### 5. Configure VS Code
1. **Open project in VS Code:**
   ```bash
   code .
   ```

2. **Select Python Interpreter:**
   - Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
   - Type "Python: Select Interpreter"
   - Choose the interpreter from your virtual environment:
     - Windows: `travel_agent_env\Scripts\python.exe`
     - macOS/Linux: `travel_agent_env/bin/python`

### 6. Run the Application
```bash
streamlit run app.py
```

The app will open automatically in your browser at: `http://localhost:8501`

## 🎯 Quick Test
1. Try searching for flights in the sidebar (e.g., "Mumbai" to "Paris")
2. Test the AI travel planner with a request like:
   ```
   I want to travel from New York to London for 5 days next month. 
   Looking for mid-range hotels and historical attractions.
   ```

## 🐛 Troubleshooting

### "streamlit command not found"
```bash
# Try this instead:
python -m streamlit run app.py
```

### Import Errors
- Make sure virtual environment is activated
- Reinstall packages: `pip install -r requirements.txt`
- Restart VS Code

### API Key Issues
- Double-check your `.env` file has correct API keys
- Ensure no extra spaces around the `=` sign
- Restart the app after changing `.env`

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

## 📁 Project Structure
```
travel-agent/
├── app.py                 # Main Streamlit application
├── .env                   # Your API keys (keep private!)
├── .env.template         # Template for environment setup
├── .streamlit/           
│   └── config.toml       # Streamlit configuration
└── LOCAL_SETUP.md        # This setup guide
```

## 🔒 Security Notes
- **Never commit your `.env` file** to version control
- Keep your API keys private
- Use `.env.template` for sharing setup instructions

## 🌐 Deployment Options
Once working locally, you can deploy to:
- **Streamlit Cloud** (free)
- **Heroku** (free tier available)
- **Railway** (simple deployment)
- **DigitalOcean App Platform**

---

✅ **Your AI Travel Agent is now ready to run locally!**