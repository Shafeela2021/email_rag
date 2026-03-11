import os.path
import sys
import time
from base64 import urlsafe_b64decode
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- GOOGLE LIBRARIES ---
# Import lightweight auth libraries immediately
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime

# Lazy import: googleapiclient.discovery.build is slow to import
# We'll import it only when needed (inside functions)


# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = "secrets/credentials.json"
TOKEN_FILE = "secrets/token.json"
MAX_EMAIL = 1

def get_credentials():
    """Load or request OAuth credentials with refresh logic."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None # Force re-login if refresh fails
        
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def extract_text_from_payload(payload):
    """Extract plain text from Gmail payload parts."""
    parts = payload.get("parts", [])
    if not parts:
        # Handle simple messages without parts
        data = payload.get("body", {}).get("data")
        if data:
            return urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
        return ""

    full_text = ""
    for part in parts:
        mime = part.get("mimeType")
        body = part.get("body", {})
        data = body.get("data")

        if mime == "text/plain" and data:
            text = urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
            full_text += text + "\n"
        elif "parts" in part:
            full_text += extract_text_from_payload(part)
    return full_text.strip()

def fetch_single_email(creds, msg_id):
    """
    Creates its own service instance to be thread-safe.
    This prevents the SSL 'Bad Record Mac' and malloc crashes.
    """
    try:
        # Lazy import to avoid slow startup
        from googleapiclient.discovery import build
        # Build local service for this thread
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
        detail = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        payload = detail.get("payload", {})
        headers = payload.get('headers', [])

        # Initialize defaults
        subject = "No Subject"
        date_str = ""

        # Extract specific headers
        for header in headers:
            name = header.get('name').lower()
            if name == 'subject':
                subject = header.get('value')
            if name == 'date':
                date_str = header.get('value')

        ms_stamp = int(detail.get('internalDate', 0))
        clean_date = datetime.datetime.fromtimestamp(ms_stamp / 1000.0).strftime('%Y-%m-%d')
        print(f'headers :{headers}')
        return {"id": msg_id, 
                "subject": subject,
                "date": clean_date,  # Use this for your metadata
                "raw_date": date_str,
                "text": extract_text_from_payload(payload),
                "headers": headers
                }
    except Exception as e:
        return {"id": msg_id, "error": str(e)}

def fetch_emails(query="", max_results=10, max_workers=5):
    """Fetches list of messages and gets details in parallel."""
    # Lazy import to avoid slow startup
    from googleapiclient.discovery import build
    
    # Main service for listing messages
    creds = get_credentials()
    main_service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    
    # fetch gmail only ids 
    results = main_service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = results.get("messages", [])

    
    if not messages:
        print("No emails found.")
        return []
    
    print(f"Syncing {len(messages)} emails using {max_workers} threads...")
    all_emails = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Pass 'creds' instead of 'service' to ensure thread-safety
        future_to_msg = {executor.submit(fetch_single_email, creds, m["id"]): m["id"] for m in messages}
        
        for i, future in enumerate(as_completed(future_to_msg), 1):
            res = future.result()
            if "error" not in res:
                all_emails.append(res)
            if i % 10 == 0 or i == len(messages):
                print(f"Progress: {i}/{len(messages)} fetched")
    
    print(f'all_emails : {all_emails[0]}')
            
    return all_emails



if __name__ == "__main__":
    try:
        print('Getting the credential ....')
        start_time = time.time()
        print('Fetching emails ....')
        emails = fetch_emails(query="Leland High", max_results=MAX_EMAIL, max_workers=10)
        
        print(f"\n✓ Completed in {time.time() - start_time:.2f} seconds")
        print(f"✓ Total emails retrieved: {len(emails)}")
        
        # Print a snippet of the first email for verification
        if emails:
            print("-" * 30)
            print(f"Sample Content: {emails[0]['text'][:100]}...")
            
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\n✗ Critical Error: {e}")