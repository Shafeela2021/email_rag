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
xattr -c /Users/shafeela/Documents/Ai_trial_cursor

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
A :The tryouts for returning and experienced players were on Friday, February 6, from 5:00 PM to 8:00 PM. The tryouts for new players were on Wednesday, February 11, from 5:00 PM to 8:00 PM and Thursday, February 12, from 6:00 PM to 9:00 PM.

Q:what are the events happening in the month of February
A:Contract to the cafeteria on Friday 13 February during tutorial.
Academic advisement session on 2/13/26 during the tutorial period in the cafeteria.
Deadline for submission of Dual Enrollment forms for SJCC Dual Enrollment courses Psychology & Sociology on 2/13/26.
Counselors will begin meeting rising seniors to input their course requests on 2/24.
Mixer Dance with Pioneer on Friday, February 27, 7-9pm at Leland.
School Site Council on 26 February 2026 at 3:30 pm in the Media Center.
Winter Social with Pioneer on 27 February 2026, 7-9pm at Leland.

Q: can you get the badminton practice schedule
A: The practice schedule mentioned in the context is as follows:
Friday 2/6 5:00 PM-8:00PM: Returning Players and Experienced Players meet in Main Gym
Wednesday 2/11 5:00 PM-8:00 PM: New players and new to the team meet in Main Gym
Thursday 2/12 6:00 PM-9:00 PM: New players and new to the team meet in Main Gym
Tuesday 2/17: First day of practice, time to be determined (TBD)
Please note that all new players must attend both days of tryouts.

Q:where can i find the badminton roaster?
A:The context does not provide information on where to find the badminton roster.

Q:where can i find the final badminton roster
A:The final badminton roster will be posted in front of room C-12 during tutorial on Friday 2/13.

Q:what is badminton coach email?
A: The email for Coach Larks, who is a badminton coach, is ALARKS@SJUSD.ORG.

Q:what to bring on badminton tryout 
A:You should bring your badminton racket, indoor gym shoes or badminton shoes, and wear athletic clothes. If you have not restrung your racket since last season, you need to get it done by tryouts.

Q:where can i purchase my racket?
A:You can purchase your racket at Badminton Alley in Sunnyvale, AK Badminton in Fremont, Racket Supply in Cupertino, or online at Joy Badminton.

Q:what is the latest information on badminton season?
A:The latest information on the badminton season is that it is about to start in 2026. Coach Mike and Coach Larks are excited for the start of the season. They have asked all players to ensure their documentation is uploaded to Register My Athlete and that physicals are approved by the athletic director, Mike Sparrer. They are finalizing the gym schedule and will send out more information soon. They have also provided a list of requirements for both new and returning players for the tryouts.

Q: When is the Varsity Boys Basketball?
A: The Varsity Boys Basketball tryout is on Monday, November 3 @ 7:30pm-9:30pm (@ Main Gym).

Q: When is the JV/Freshman Boys Basketball?
A: The JV/Freshman Boys Basketball tryout is on Saturday, November 8 from 9am-12pm (@ Main Gym).

Q: When is the last day of course registration for sophomores/rising juniors 2026-27?
A: The requests for courses will be locked on 3/31/26 at 3:20 pm.

Q: When is the wellness week?

Q: when is 11th Grade Parent Night?"
A: 11th Grade Parent Night will be held on March 12, 2026, at 6:00 PM in the Cafeteria.

Q: when is End-of-Year Chromebook Collection?"
A: End-of-Year Chromebook Collection for Leland High School Students will begin as we approach the end of the 2025–26 school year.
    
Q: Any info about new SJUSD new math curriculum
A: Savvas Learning Company is the publisher of enVision+ California (Algebra 1, Geometry, Algebra 2), a comprehensive curriculum aligned with the 2023 California Mathematics Framework and the California Common Core State Standards. It provides students with robust problem-solving structures and consistent, standards-aligned instruction necessary to develop mathematical reasoning, procedural fluency, data analysis skills, and deep conceptual understanding.
    
Q: When is Badminton tryout?
A: Badminton tryouts are on Tuesday, February 11 & Wednesday, February 12 from 5:00 PM-8:00 PM and Thursday, February 12 from 6:00 PM-9:00 PM.

Q: Why is the  student-led walkout  at Leland High happened'
A: The student-led walkout at Leland High School was held to express student voice and civic engagement.

Q: can you get the badminton practice schedule?
A: The Badminton tryout schedule for the week of Feb 16th is: Mon 2/16 6:00-8:00
    Thurs 2/19 6:00-8:00
