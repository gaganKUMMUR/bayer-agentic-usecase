# bayer-agentic-usecase
# Tech News Digest Pipeline (LangGraph Agent-Based)

A three-agent LangGraph pipeline that:

1. **FetchAgent**: Retrieves today's top tech headlines from NewsAPI and stores them in state.
2. **SummarizerAgent**: Reads the headlines, calls Google Gemini to generate a 5-bullet summary, and updates state.
3. **EmailAgent**: Reads the summary and sends it via Gmail SMTP to a specified recipient.

Everything is orchestrated via a `StateGraph` in `pipeline.py`, with environment variables managed through a `.env` file.

---

## Prerequisites

* **Python 3.8+**
* A **NewsAPI** key (sign up at [https://newsapi.org](https://newsapi.org))
* A **Google Cloud** API key with the **Generative Language API** enabled
* A **Gmail** account with **2‑Step Verification** enabled (for App Passwords)

---

## Installation

1. **Create a `requirements.txt`** file in the project root with the following contents:

   ```text
   langgraph
   requests
   typing-extensions
   ```

2. **Clone or download** this repository:

   ```bash
   git clone https://github.com/yourusername/tech-news-digest.git
   cd tech-news-digest/DailyNewsDigest
   ```

3. **Create and activate** a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **Install dependencies** from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

---

## Generating API Keys and App Password and App Password and App Password

### NewsAPI Key

1. Go to [https://newsapi.org](https://newsapi.org) and sign up for a free account.
2. Copy your **API key** from your dashboard.

### Google Cloud Generative Language API Key

1. Visit the Google Cloud Console: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
2. Enable the **Generative Language API**.
3. Go to **Credentials → Create Credentials → API key**.
4. Copy the generated key.

### Gmail App Password

1. Go to your Google Account security settings: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Under **"Signing in to Google"**, turn **2‑Step Verification** **On** if it isn’t already.
3. Click **App passwords**.
4. Select **Mail** as the app, **Other (Custom name)** as the device, and name it (e.g. `NewsDigestScript`).
5. Click **Generate** and copy the 16‑character password (no spaces).

---

## Configuration

1. Create a file named `.env` in the project root (`DailyNewsDigest/`) with the following contents:

   ```env
   NEWS_API_KEY=your_newsapi_key_here
   GEMINI_API_KEY=your_google_api_key_here
   FROM_EMAIL=your.email@gmail.com
   FROM_EMAIL_PASS=your_16_char_app_password_here
   TO_EMAIL=recipient.email@example.com
   ```

2. The top of `pipeline.py` already includes:

   ```python
   from dotenv import load_dotenv
   load_dotenv()  # loads variables from .env into os.environ
   ```

---

## Running the Pipeline

With your virtual environment active and `.env` in place, run:

```bash
cd path/to/tech-news-digest/DailyNewsDigest
python pipeline.py
```

You should see:

```
📬 Digest sent!
```

Check the recipient inbox to confirm arrival of the 5-bullet tech news summary.

---

## Automation

You can schedule the pipeline to run automatically every day at 8 AM using `cron` on macOS or Linux.

1. Open your crontab for editing:

   ```bash
   crontab -e
   ```

2. Add this line at the end (replace the paths with your actual project and Python executable paths):

   ```cron
   # Run Tech News Digest daily at 8:00 AM
   0 8 * * * cd /Users/yourusername/tech-news-digest/DailyNewsDigest && /Users/yourusername/tech-news-digest/DailyNewsDigest/.venv/bin/python pipeline.py >> /Users/yourusername/tech-news-digest/DailyNewsDigest/pipeline.log 2>&1
   ```

   * `0 8 * * *` means “at minute 0 of hour 8 every day.”
   * `cd ...` changes to your project directory.
   * The full path to your `.venv`’s Python ensures the correct interpreter.
   * Output (both stdout and stderr) is redirected to `pipeline.log` for later review.

3. Save and exit the editor. Your cron job is now active.

---

## Troubleshooting

* **401 Unauthorized from NewsAPI**: Verify `NEWS_API_KEY` in `.env` and ensure it's valid.
* **400/404 from Gemini**: Check `GEMINI_API_KEY`, ensure the Generative Language API is enabled, and the URL matches `/v1beta/models/gemini-2.0-flash:generateContent`.
* **SMTP AuthenticationError**: Confirm you used a valid 16-character Gmail App Password (no spaces) and that 2‑Step Verification is on.

---

© MIT Licensed
