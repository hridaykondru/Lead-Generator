# README — `leadGenerator.py`

## What it does
Reads a CSV of influencer profiles, filters by **category**, asks Gemini (Google Generative Language API, model *gemini-2.5-flash*) to pick the **top K** and draft personalized emails, then sends those emails via SMTP.

**Why influencer data?** The AI ranks outreach targets and personalizes copy; richer profile data → better targeting and higher response odds.

## Data it uses
Create `influencers.csv` in the same folder.

- **Minimum columns to mail someone:** `category`, `email`, `full_name` (or `username`)  
- **Recommended (improves ranking/personalization):** `followers`, `engagement`, `avg_likes`, `avg_comments`, `follower_growth_rate`, `country`, `age`, `gender`, `id`

## Env vars (create `variables.env` next to the script)
```
email_address=your.name@example.com      # NO quotes
email_password="your_email_app_password" # MUST be in "double quotes"
gemini_api_key=YOUR_GEMINI_API_KEY       # NO quotes
```
- Uses Gmail by default (`smtp.gmail.com:587` + STARTTLS). For Gmail, use an **App Password**.
- If credentials are missing or placeholder, the script **prints** emails instead of sending.

## Install
```bash
pip install pandas requests python-dotenv
```

## Run
```bash
python leadGenerator.py
```
You’ll be prompted for the **category** and **K** (how many influencers to contact). Adjust `SMTP_SERVER`/`SMTP_PORT` in the file if not using Gmail.
