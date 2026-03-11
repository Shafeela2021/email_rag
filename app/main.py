import time
from app.gmail import fetch_emails
from app.rag import EmailRAG
from datetime import date
import gradio as gr

import os


rag = EmailRAG()
is_generate_data = True

def chat_fn(user_message, history=None):
    """
    user_message: str - user question
    history: list of tuples (user, bot)
    """
    if history is None:
        history = []

    # Add today's date automatically if you want
    question = f"{user_message}"
    answer = rag.ask(question)
    return str(answer)

SYNC_TRACKER = "app/last_sync.txt"

def should_i_sync():
    today = date.today().isoformat() # e.g., "2026-02-15"
    
    if os.path.exists(SYNC_TRACKER):
        with open(SYNC_TRACKER, "r") as f:
            last_date = f.read().strip()
            if last_date == today:
                return False # Already synced today!
                
    return True 

import time
from datetime import date
import gradio as gr

def run_pipeline(search_query="Leland high", limit=100):
    total_start = time.time()
    rag = EmailRAG() # Ensure RAG is initialized for both sync and chat

    # 1. 🔹 Check if we need to sync (Added parentheses to call the function)
    if should_i_sync():
        try:
            print("\n" + "=" * 60)
            print("EMAIL RAG PIPELINE - SYNCING DATA")
            print("=" * 60)

            # 🔹 Step 2: Fetch Emails
            print(f"\n[1] Fetching emails for query: '{search_query}'")
            fetch_start = time.time()
            emails = fetch_emails(query=search_query, max_results=limit, max_workers=10)
            print(f"✓ Fetched {len(emails)} emails ({time.time() - fetch_start:.2f}s)")

            if not emails:
                print("No emails found.")
            else:
                # 🔹 Step 3: Index Emails
                print("\n[2] Indexing emails...")
                index_start = time.time()
                docs, ids = rag.process_email(emails)
               
                print("\n process_save_rag...")
                rag.process_save_rag(docs, ids)
                print(f"✓ Indexed ({time.time() - index_start:.2f}s)")

                # 🔹 Step 4: Success! Save the date
                with open(SYNC_TRACKER, "w") as f:
                    f.write(date.today().isoformat())
                print(f"✅ Tracker updated. Total Time: {time.time() - total_start:.2f}s")

        except Exception as e:
            print(f"\n✗ Pipeline error during sync: {e}")
            # We don't return here so that the UI can still launch with old data
    else:
        print("\n" + "=" * 60)
        print("✅ RAG IS UP TO DATE. SKIPPING FETCH.")
        print("=" * 60)

    # 2. 🔹 Launch Gradio (Moved OUTSIDE the if-block so it always runs)
    print("\n[3] Launching Chat Interface...")
    try:
        def chat_fn(message, history):
            return rag.ask(message)

        with gr.Blocks() as demo:
            gr.Markdown("## 🦅 Leland High Gmail RAG Chatbot")
            gr.ChatInterface(fn=chat_fn)
            
        demo.launch()
    except Exception as e:
        print(f"✗ UI Error: {e}")

if __name__ == "__main__":
    run_pipeline()