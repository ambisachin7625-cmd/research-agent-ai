# 🚀 ResearchAI - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd miniagent
pip install -r requirements.txt
```

### 2. Verify Environment
The `.env` file should already have your API keys configured:
```
OPENAI_API_KEY=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
OPENAI_MODEL=llama-3.1-8b-instant
OPENAI_BASE_URL=https://api.groq.com/openai/v1
TAVILY_API_KEY=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
```

### 3. Start Local Server
```bash
python app.py
```

You should see:
```
==================================================
  ResearchAI is running!
  Local:  http://127.0.0.1:5000
  Links:  http://127.0.0.1:5000/api/links?q=your+topic
==================================================
```

### 4. Test the Links API

**Using Python test script:**
```bash
python test_links_api.py --query "python projects" --max 5
```

**Using cURL:**
```bash
curl "http://127.0.0.1:5000/api/links?q=machine+learning&max=3"
```

**Using PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/links?q=react+github" -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Using Python requests:**
```python
import requests

response = requests.get(
    "http://127.0.0.1:5000/api/links",
    params={"q": "tensorflow", "max": 5, "validate": False}
)
print(response.json())
```

---

## 📊 API Response Example

Query: `http://localhost:5000/api/links?q=github+projects&max=3`

Response:
```json
{
  "query": "github projects",
  "count": 3,
  "links": [
    {
      "title": "About Projects - GitHub Docs",
      "url": "https://docs.github.com/issues/planning-and-tracking-with-projects",
      "snippet": "A project is an adaptable table, board, and roadmap...",
      "domain": "docs.github.com",
      "score": 4,
      "quality": "Blog / Standard Site",
      "live": null
    }
  ]
}
```

---

## 🔧 Common Queries to Test

```bash
# Python libraries
python test_links_api.py --query "python machine learning libraries"

# JavaScript frameworks
python test_links_api.py --query "react vue next.js frameworks"

# Open source projects
python test_links_api.py --query "github open source projects"

# With URL validation (slower but checks if links are live)
python test_links_api.py --query "github" --validate

# Full test suite
python test_links_api.py --full-test
```

---

## 📦 What Each File Does

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application & web server |
| `link_fetcher.py` | Core link extraction & validation logic |
| `search.py` | Tavily search client integration |
| `scraper.py` | Web scraping & source quality scoring |
| `agent.py` | AI research orchestration |
| `database.py` | User & chat history management |
| `config.py` | Configuration & environment loading |
| `auth.py` | Authentication & user management |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container configuration |
| `render.yaml` | Render.com deployment config |
| `test_links_api.py` | Testing script (this is helpful!) |

---

## 🌐 Web Interface

Once running, visit:
- **Home**: http://localhost:5000
- **Links Page**: http://localhost:5000/links
- **Login**: http://localhost:5000/login
- **Register**: http://localhost:5000/register

Default credentials (for testing):
- Username: `admin`
- Password: `password` (if pre-configured)

---

## 🐛 Troubleshooting

### "TAVILY_API_KEY not set"
- Check `.env` file exists in project root
- Verify `TAVILY_API_KEY=...` is present
- Restart the server

### "Connection refused on localhost:5000"
- Make sure Flask server is running (`python app.py`)
- Check port 5000 is not in use: `netstat -ano | findstr :5000`
- Try a different port: `PORT=8000 python app.py`

### "Empty results from links API"
- Check internet connection
- Verify Tavily API key is valid
- Try a different search query
- Check server logs for errors

### "Links taking too long to fetch"
- Use `validate=false` to skip URL validation
- Reduce `max_results` parameter
- Check server CPU/memory usage

---

## 📈 Next Steps

1. **Test the web interface**: Visit http://localhost:5000
2. **Try research feature**: Ask questions to the AI
3. **Export reports**: Generate PDF/Markdown reports
4. **Deploy to cloud**: See DEPLOYMENT_GUIDE.md
5. **Customize**: Modify config.py for your needs

---

## 🚀 Deploy to Cloud (Render.com)

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/miniagent.git
git push -u origin main

# 3. On Render.com:
# - Create new Web Service
# - Connect GitHub repository
# - Environment variables auto-loaded from render.yaml
# - Deploy!
```

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

---

## 📞 Need Help?

- Check logs: `tail -f researchai.db.log`
- Read DEPLOYMENT_GUIDE.md for production setup
- Review test_links_api.py for API examples
- Check Flask documentation: https://flask.palletsprojects.com

---

**Happy researching! 🎉**
