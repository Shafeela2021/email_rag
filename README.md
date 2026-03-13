# My RAG Bot Project

This project implements a Retrieval-Augmented Generation (RAG) system using LangChain and the Gmail API.

---

## 🚀 Environment Setup (Using UV)

Follow these steps to set up the Python environment using the `uv` package manager.

### 1. Initialize Project
```bash
mkdir my-uv-project
cd my-uv-project
uv init

# Fix macOS quarantine errors
xattr -c ~/Documents/Ai_trial_cursor

# Install and pin specific Python version
brew install python@3.12
uv python pin /usr/local/bin/python3.12

# Create and activate venv
rm -rf .venv      # remove old quarantined venv
uv venv
source .venv/bin/activate

uv add requests pytest google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client langchain-openai langgraph gradio
uv sync   # run whenever you open/close the project to stay synced

---

## ⚡ Running the Script (Faster Alternative to `uv run`)

**Why `uv run` can be slow:**
- `uv run` resolves and syncs dependencies on every execution
- This adds significant overhead (5-30+ seconds) before your script even starts

**Faster alternatives:**

### Option 1: Use Virtual Environment Directly (Recommended)
```bash
# One-time setup: Create and sync environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Then run directly (much faster!)
python main.py
# or
python gmail.py
```

### Option 2: Pre-sync with `uv run`
```bash
# Sync dependencies first (one-time or when dependencies change)
uv sync

# Then uv run will be faster (but still slower than direct python)
uv run main.py
```

### Option 3: Use `uv run --no-sync` (if available in your uv version)
```bash
uv run --no-sync main.py  # Skips dependency resolution
```

**Recommendation:** Use Option 1 for fastest startup times during development.

---

## 🔐 Google Cloud Setup (Gmail API)

To allow the bot to access Gmail, you must configure a Google Cloud Project and obtain credentials.

### 1. Create a Project

- Go to the Google Cloud Console.
- Click the project dropdown in the top left and select "New Project".
- Name it (e.g., "My RAG Bot") and click Create.

### 2. Enable the Gmail API

- In the left-hand sidebar, go to APIs & Services > Library.
- Search for "Gmail API".
- Click it and then click the Enable button.

### 3. Configure the OAuth Consent Screen

- Go to APIs & Services > OAuth consent screen.
- Select External (unless you are in a Workspace organization).
- Fill in the required fields: App name, User support email, and Developer contact info.
- **CRUCIAL**: Navigate to the "Test Users" section and add your own Gmail address. The login will fail otherwise.

### 4. Create Credentials

- Go to APIs & Services > Credentials.
- Click + CREATE CREDENTIALS and select OAuth client ID.
- For Application type, select Desktop app.
- Click Create, then click DOWNLOAD JSON from the pop-up.

### 5. Rename and Move

- Rename the downloaded file to exactly `credentials.json`.
- Move it into your `my-uv-project` root folder.


### List of question to asked:

Q : when is the badminton tryout?

Q: can you get the badminton practice schedule

Q:what to bring on badminton tryout 

Q:where can i purchase my racket?

Q: When is the Varsity Boys Basketball?

Q: When is the JV/Freshman Boys Basketball?
