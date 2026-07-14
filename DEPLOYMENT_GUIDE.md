# ResearchAI - Live Project Link Extraction Deployment Guide

## 📋 Project Overview

**ResearchAI** is a Flask-based web application that:
- Performs AI-powered research on any topic
- Extracts and fetches **live project links** via the `/api/links` endpoint
- Stores chat history for authenticated users
- Exports research reports (PDF, DOCX, Markdown, TXT)
- Validates URL availability in real-time

## 🔑 Key Features

### Live Link Extraction API
- **Endpoint**: `/api/links` (GET/POST)
- **Purpose**: Search for project links and validate their availability
- **Query Parameters**:
  - `q` or `query`: Search term (required)
  - `max`: Maximum results (default: 3 for fast mode, 5 for normal)
  - `validate`: Ping URLs to confirm they're live (default: true)

### Example Requests
```bash
# GET request
curl "http://localhost:5000/api/links?q=machine+learning&max=5&validate=true"

# POST request
curl -X POST http://localhost:5000/api/links \
  -H "Content-Type: application/json" \
  -d '{"query": "python web framework", "max_results": 5, "validate": true}'
```

### Response Format
```json
{
  "query": "machine learning",
  "count": 3,
  "links": [
    {
      "title": "TensorFlow - Machine Learning Library",
      "url": "https://tensorflow.org",
      "snippet": "TensorFlow is an open-source machine learning framework...",
      "domain": "tensorflow.org",
      "score": 95,
      "quality": "High Quality",
      "live": true
    }
  ]
}
```

---

## 🚀 Deployment Options

### Option 1: Local Deployment (Development)

#### Prerequisites
- Python 3.12+
- pip (Python package manager)

#### Steps

1. **Clone/Navigate to project**
   ```bash
   cd C:\Users\Harshal\Desktop\miniagent
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify `.env` file**
   ```bash
   # Check that .env contains:
   # - OPENAI_API_KEY (Groq or OpenAI)
   # - TAVILY_API_KEY (required for search)
   # - Other optional configs
   ```

5. **Run development server**
   ```bash
   python app.py
   ```
   Output:
   ```
   ================================================== 
     ResearchAI is running!
     Local:  http://127.0.0.1:5000
     Links:  http://127.0.0.1:5000/api/links?q=your+topic
   ==================================================
   ```

6. **Test the API**
   ```bash
   curl "http://127.0.0.1:5000/api/links?q=github+projects&max=3&validate=false"
   ```

---

### Option 2: Docker Deployment

#### Prerequisites
- Docker installed and running

#### Steps

1. **Build Docker image**
   ```bash
   cd C:\Users\Harshal\Desktop\miniagent
   docker build -t researchai:latest .
   ```

2. **Run container locally**
   ```bash
   docker run \
     -p 5000:5000 \
     -e OPENAI_API_KEY="your-key-here" \
     -e TAVILY_API_KEY="your-tavily-key" \
     -e FAST_RESEARCH="true" \
     researchai:latest
   ```

3. **Test container**
   ```bash
   curl "http://localhost:5000/api/links?q=docker+projects"
   ```

---

### Option 3: Render.com Deployment (Recommended for Production)

#### Prerequisites
- GitHub account
- Render.com account (free tier available)

#### Steps

1. **Push code to GitHub**
   ```bash
   cd C:\Users\Harshal\Desktop\miniagent
   git init
   git add .
   git commit -m "Initial ResearchAI deployment"
   git remote add origin https://github.com/YOUR_USERNAME/miniagent.git
   git branch -M main
   git push -u origin main
   ```

2. **Connect to Render.com**
   - Go to https://render.com
   - Sign up / Log in
   - Click "New +" → "Web Service"
   - Select "Build and deploy from a Git repository"
   - Connect your GitHub account
   - Select the `miniagent` repository

3. **Configure Deployment**
   - Use the `render.yaml` file (already in project)
   - Environment variables will be auto-configured:
     - `OPENAI_API_KEY` (input your Groq/OpenAI key)
     - `TAVILY_API_KEY` (input your Tavily key)
     - `SECRET_KEY` (auto-generated)
     - `FAST_RESEARCH=true` (pre-configured for free tier)

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - URL will be something like: `https://researchai-XXXXX.onrender.com`

5. **Verify Deployment**
   ```bash
   curl "https://researchai-XXXXX.onrender.com/health"
   curl "https://researchai-XXXXX.onrender.com/api/links?q=react+projects"
   ```

---

### Option 4: Heroku Deployment

#### Prerequisites
- Heroku CLI installed
- Heroku account

#### Steps

1. **Create Procfile** (already exists)
   ```
   web: gunicorn app:app
   ```

2. **Create Heroku app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Set environment variables**
   ```bash
   heroku config:set OPENAI_API_KEY="your-key"
   heroku config:set TAVILY_API_KEY="your-tavily-key"
   heroku config:set SECRET_KEY="random-secret-key"
   heroku config:set FAST_RESEARCH="true"
   heroku config:set DATABASE_PATH="/tmp/researchai.db"
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **View logs**
   ```bash
   heroku logs --tail
   ```

---

## 📊 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | API key for LLM (Groq, OpenAI, etc.) |
| `OPENAI_MODEL` | gpt-4o-mini | LLM model to use |
| `OPENAI_BASE_URL` | - | Custom base URL (for Groq, Ollama, etc.) |
| `TAVILY_API_KEY` | Required | Search API key |
| `SECRET_KEY` | dev-secret | Flask session secret (set in production) |
| `DATABASE_PATH` | researchai.db | SQLite database location |
| `FAST_RESEARCH` | true | Faster results, fewer iterations |
| `MAX_ITERATIONS` | 2 (fast) / 5 | Research iterations |
| `MAX_SEARCH_RESULTS` | 3 (fast) / 5 | Default search results |
| `MAX_SCRAPE_PER_QUERY` | 1 (fast) / 2 | Pages to scrape per search |
| `CONFIDENCE_THRESHOLD` | 70 (fast) / 80 | Minimum confidence % |
| `SKIP_IMAGES` | true | Skip image generation (fast mode) |

---

## 🧪 API Testing

### Test Link Extraction Without Validation
```bash
curl "http://localhost:5000/api/links?q=python+libraries&max=5&validate=false"
```

### Test Link Extraction With Validation
```bash
curl "http://localhost:5000/api/links?q=react+github&max=3&validate=true"
```

### Test Health Endpoint
```bash
curl "http://localhost:5000/health"
```

### Python Test Script
```python
import requests

# Fetch live links
response = requests.get(
    "http://localhost:5000/api/links",
    params={
        "q": "tensorflow machine learning",
        "max": 5,
        "validate": True
    }
)

data = response.json()
print(f"Found {data['count']} links:")
for link in data['links']:
    print(f"  - {link['title']} ({link['url']})")
    print(f"    Quality: {link['quality']}, Live: {link['live']}")
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use environment variables** for all secrets
3. **Set `SECRET_KEY` in production** - Use random string
4. **Use HTTPS** in production (auto on Render/Heroku)
5. **Validate user input** - Already implemented
6. **Rate limiting** - Consider adding for production

---

## 🐛 Troubleshooting

### Issue: `TAVILY_API_KEY` not found
- Ensure `.env` file exists in project root
- Check that `TAVILY_API_KEY` is set
- Restart the application

### Issue: Links API returns empty results
- Check internet connection
- Verify `TAVILY_API_KEY` is valid and has credits
- Try a different search query
- Check server logs for errors

### Issue: URLs not validating (validation=true)
- Network timeout is normal for slow URLs
- Try with `validate=false`
- Check firewall/proxy settings

### Issue: Render deployment fails
- Check build logs in Render dashboard
- Ensure `render.yaml` is in root directory
- Verify environment variables are set

---

## 📈 Performance Tuning

### For Fast Responses
```env
FAST_RESEARCH=true
MAX_ITERATIONS=2
MAX_SEARCH_RESULTS=3
SKIP_IMAGES=true
```

### For Comprehensive Results
```env
FAST_RESEARCH=false
MAX_ITERATIONS=5
MAX_SEARCH_RESULTS=5
SKIP_IMAGES=false
```

---

## 📞 Support

- **Tavily API Docs**: https://tavily.com/api
- **Flask Docs**: https://flask.palletsprojects.com
- **Groq (LLM)**: https://groq.com
- **Render Docs**: https://render.com/docs

---

## ✅ Deployment Checklist

- [ ] Clone/download project
- [ ] Create `.env` file with API keys
- [ ] Test locally (`python app.py`)
- [ ] Test `/api/links` endpoint
- [ ] Choose deployment platform
- [ ] Deploy (Docker / Render / Heroku)
- [ ] Test production endpoint
- [ ] Set up monitoring/alerts
- [ ] Document API in team wiki

---

**Last Updated**: 2024
**Version**: 1.0
