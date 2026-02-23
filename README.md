# InvestIQ AI — Complete Deployment Guide

## Prerequisites Checklist
- [ ] Python 3.10+ installed locally
- [ ] GitHub account
- [ ] Firebase account (free)
- [ ] Groq account (free) → https://console.groq.com
- [ ] Google AI Studio account (free) → https://aistudio.google.com

---

## STEP 1 — Get Your API Keys

### Groq API Key (Free)
1. Go to https://console.groq.com
2. Sign up / Sign in
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key → save it

### Gemini API Key (Free)
1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Select any Google Cloud project (or create one)
4. Copy the key → save it

---

## STEP 2 — Firebase Setup

### 2a. Create Firebase Project
1. Go to https://console.firebase.google.com
2. Click **Add project**
3. Name it: `investiq-ai` (or anything)
4. Disable Google Analytics (not needed)
5. Click **Create project**

### 2b. Enable Authentication
1. In Firebase Console → click **Authentication** (left sidebar)
2. Click **Get started**
3. Click **Email/Password** → Enable → Save
4. *(Optional)* Click **Google** → Enable → Save (for Google sign-in)

### 2c. Create Firestore Database
1. In Firebase Console → click **Firestore Database** (left sidebar)
2. Click **Create database**
3. Select **Start in production mode**
4. Choose a region (e.g. `us-east1` or closest to you)
5. Click **Enable**

### 2d. Set Firestore Security Rules
1. In Firestore → click **Rules** tab
2. Replace everything with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/analyses/{analysisId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == userId;
    }
    match /{path=**}/analyses/{analysisId} {
      allow read: if resource.data.is_public == true;
    }
  }
}
```

3. Click **Publish**

### 2e. Get Firebase Web Config
1. In Firebase Console → click the **gear icon** → **Project settings**
2. Scroll to **Your apps** section
3. Click **</>** (Web) icon
4. Register app name: `investiq-web`
5. Do NOT enable Firebase Hosting
6. Click **Register app**
7. Copy the `firebaseConfig` object — you'll need all values

---

## STEP 3 — Configure secrets.toml

Edit `.streamlit/secrets.toml` with your real values:

```toml
[groq]
api_key = "gsk_your_groq_key_here"

[google]
api_key = "AIza_your_gemini_key_here"

[firebase]
apiKey = "AIza_your_firebase_api_key"
authDomain = "your-project-id.firebaseapp.com"
projectId = "your-project-id"
storageBucket = "your-project-id.appspot.com"
messagingSenderId = "123456789"
appId = "1:123456789:web:abc123"
databaseURL = ""

[app]
base_url = "https://your-app-name.streamlit.app"
```

**⚠️ IMPORTANT:** Never commit secrets.toml to GitHub.
The `.gitignore` already excludes it.

---

## STEP 4 — Test Locally

```bash
# 1. Create virtual environment
python -m venv venv

# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run main.py
```

Open http://localhost:8501 in your browser.

**Test checklist:**
- [ ] Home page loads with demo analysis
- [ ] Sign up with email works
- [ ] Analysis form submits and agents run
- [ ] Score dashboard renders
- [ ] Save to Firestore works
- [ ] PDF downloads
- [ ] History page shows saved analyses
- [ ] Compare page works with 2+ analyses

---

## STEP 5 — Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Verify secrets.toml is NOT being added
git status
# Should NOT show .streamlit/secrets.toml

# Commit
git commit -m "Initial InvestIQ AI deployment"

# Create GitHub repo at github.com → New Repository
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/investiq-ai.git
git branch -M main
git push -u origin main
```

---

## STEP 6 — Deploy to Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click **New app**
4. Select:
   - **Repository:** your-username/investiq-ai
   - **Branch:** main
   - **Main file path:** main.py
5. Click **Advanced settings**
6. In the **Secrets** box, paste your ENTIRE `secrets.toml` content
7. Click **Save**
8. Click **Deploy!**

Wait 2-3 minutes for the first build.

### After Deploy:
1. Copy your app URL (e.g. `https://investiq-ai.streamlit.app`)
2. Update `secrets.toml` → `[app] base_url` with this URL
3. In Streamlit Cloud → App settings → Secrets → update `base_url`

### Add Streamlit URL to Firebase Auth:
1. Firebase Console → Authentication → Settings
2. Click **Authorized domains** tab
3. Click **Add domain**
4. Add: `your-app-name.streamlit.app`
5. Click **Add**

---

## STEP 7 — Verify Production

Go to your live URL and test:

- [ ] Home page loads
- [ ] Sign up works
- [ ] Analysis runs (check all 6 agents complete)
- [ ] Save works
- [ ] PDF downloads
- [ ] Share link works (open in incognito — no login required)
- [ ] History and Compare pages work

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Firebase Auth fails in production
- Add your Streamlit URL to Firebase → Authentication → Authorized domains

### Firestore save returns None
- Check Firestore rules are published
- Check id_token is valid (user is logged in)
- Check `projectId` in secrets.toml matches your Firebase project

### Groq API errors
- Verify `api_key` in secrets.toml starts with `gsk_`
- Check Groq console for usage limits

### Gemini API errors
- Verify Google API key is enabled for "Generative Language API"
- Go to Google Cloud Console → APIs → Enable "Generative Language API"

### PDF export fails
- Run: `pip install reportlab`
- Check requirements.txt includes `reportlab>=4.1.0`

### App is slow on first load
- Normal — Streamlit Community Cloud cold starts take 30-60 seconds
- Subsequent loads are faster

---

## File Structure Reference

```
investiq/
├── main.py                    ← App entry point + navigation
├── requirements.txt           ← Python dependencies
├── .gitignore                 ← Excludes secrets
├── DEPLOYMENT.md              ← This file
│
├── .streamlit/
│   └── secrets.toml           ← API keys (never commit!)
│
├── styles/
│   └── theme.py               ← Full CSS dark theme
│
├── auth/
│   └── firebase_auth.py       ← Login, signup, logout, session
│
├── ai/
│   ├── agents.py              ← 6 agent prompts + API calls
│   └── pipeline.py            ← Sequential execution orchestrator
│
├── components/
│   ├── gauge.py               ← Plotly score gauge
│   ├── radar.py               ← Plotly radar chart
│   ├── score_cards.py         ← Score cards, SW panels, deep dive
│   ├── agent_loader.py        ← Animated loading screen
│   └── pdf_export.py          ← ReportLab PDF generator
│
├── db/
│   └── firestore.py           ← All Firestore CRUD operations
│
└── pages/
    ├── home.py                ← Landing + demo dashboard
    ├── analyze.py             ← Form + pipeline + dashboard
    ├── history.py             ← Saved analyses grid
    ├── compare.py             ← Side-by-side comparison
    └── shared.py              ← Public read-only view
```

---

## Support

If any step fails, check:
1. All secrets in `secrets.toml` have correct values
2. Firebase Authorized Domains includes your Streamlit URL
3. Firestore rules are published (not just saved)
4. requirements.txt is committed to GitHub