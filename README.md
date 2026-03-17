# 🥗 FoodieMeasure AI

> Smart nutrition analyzer for Gout patients — powered by Google Gemini AI

Upload or take a photo of any food and instantly get:
- 🟢🟡🔴 Purine level (Low / Medium / High)
- 🔥 Estimated calories
- ⚗️ Estimated purine content (mg/100g)
- 🛡️ Gout safety score (1–10)
- 🥄 Safe portion size recommendation
- 💊 Personalized dietary advice for Gout patients
- 📋 Scan history (current session)

---

## 🚀 Deploy to Streamlit Cloud (Free)

### Step 1 — Push this repo to GitHub
Make sure your GitHub repository contains these files:
```
app.py
requirements.txt
README.md
.streamlit/config.toml
```

### Step 2 — Get your Google Gemini API Key (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API key**
3. Select your project (`FoodiemeasureAI`)
4. Copy the API key — you will need it in Step 4

> ✅ No billing required. The free tier is fully functional for personal use.

### Step 3 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select your repository: `luanle7290/foodiemeasureAI`
5. Branch: `main`
6. Main file: `app.py`
7. Click **Deploy!**

### Step 4 — Add your API Key as a Secret
After deploying (or before clicking Deploy):
1. In Streamlit Cloud, go to your app → **Settings** → **Secrets**
2. Add this exactly:
```toml
GOOGLE_API_KEY = "paste-your-key-here"
```
3. Click **Save** — the app will restart automatically

That's it! Your app is live. 🎉

---

## 💻 Run Locally

```bash
# Clone the repo
git clone https://github.com/luanle7290/foodiemeasureAI.git
cd foodiemeasureAI

# Install dependencies
pip install -r requirements.txt

# Create local secrets file
mkdir .streamlit
echo 'GOOGLE_API_KEY = "your-key-here"' > .streamlit/secrets.toml

# Run the app
streamlit run app.py
```

---

## 🆓 Free Tier Limits (Google Gemini)

| Limit | Value |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | ~1,000 RPD |
| Cost | $0 |
| Credit card required | No |

More than enough for personal and family use.

---

## ⚠️ Disclaimer

This app is for **informational purposes only**. Always consult a licensed physician or dietitian for medical advice regarding Gout management.

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io) — UI framework & hosting
- [Google Gemini API](https://ai.google.dev) — AI vision & analysis (free tier)
- [Pillow](https://pillow.readthedocs.io) — Image processing
- Python 3.10+
