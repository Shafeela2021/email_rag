from pydoc import Doc
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter  
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
from langdetect import detect
import chromadb
import os
import random
import re


base_dir = os.path.dirname(os.path.abspath(__file__))
persist_dir = os.path.join(base_dir, "chroma_db")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REMOTE_URL = "http://192.168.1.75:11434"

class EmailRAG:
    def __init__(self):
    #     self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY,model="text-embedding-3-large")
        
  
    #     self.text_splitter = RecursiveCharacterTextSplitter(
    #         chunk_size = 2000,
    #         chunk_overlap = 400
    #     )

        self.embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=REMOTE_URL
        )

        self.llm = ChatOllama(
        model="llama3.2",
        temperature=0,
        base_url=REMOTE_URL
        )
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200
        )

        # Load existing vectorstore if it exists
        self.vectorstore = Chroma(
            client = self.client,
            embedding_function=self.embeddings,
            collection_name="email_rag_nomic"
        )
    

    def remove_non_english(self, text):
        lines = text.split("\n")
        english_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                if detect(line) == "en":
                    english_lines.append(line)
            except:
                english_lines.append(line)

        return " ".join(english_lines)



    def clean_email(self, emails):
        # 1. Handle potential dict or direct string input
        raw_html = emails.get('text', '') if isinstance(emails, dict) else str(emails)
        
        # 2. HTML Cleanup
        soup = BeautifulSoup(raw_html, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        clean_text = soup.get_text(separator=' ')

        # 3. Targeted ParentSquare & System Noise Removal
        noise_patterns = [
            # Remove the ParentSquare "visit https://www.parentsquare.com/..." block
            r"You received this email because you are a ParentSquare user.*",
            # Remove the "Daily digest created for..." headers
            r"Daily digest created for.*?\-+\s?",
            # Remove the "Posted by... in LELAND HIGH" meta info
            r"Posted by.*?in LELAND HIGH",
            # Remove "To see the post in ParentSquare, visit..."
            r"To see the post in ParentSquare, please visit.*",
            # Remove common "Shadowing Event" or "Shadowing Program" boilerplate if needed
            r"If you received this email in error or wish to disable your account.*",
            r"You received this message because.*",
            r"To unsubscribe.*",
            r"Google Groups.*",
            r"View this discussion.*",
        ]
        
        for pattern in noise_patterns:
            clean_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove non english text
        clean_text = self.remove_non_english(clean_text)
        # Remove signature blocks
        clean_text = re.split(r'\n--\s*\n', clean_text)[0]

        # 4. CRITICAL: Remove all long URLs
        # This prevents the embedding model from focusing on random characters
        clean_text = re.sub(r'https?://\S+', ' [LINK] ', clean_text)

        # 5. Final Polish
        # Removes double dashes, extra spaces, and newlines
        clean_text = re.sub(r'\-{2,}', '', clean_text)
        clean_text = " ".join(clean_text.split())
        
        return clean_text


    def process_email(self, emails):
        docs = []
        ids = []

        for mail in emails:
            print(f'mail :{mail}')

            if mail.get("text") and mail["text"].strip():
                cleaned_email = self.clean_email(mail)
                # chunks = self.text_splitter.split_text(mail["text"])
                chunks = self.text_splitter.split_text(cleaned_email)

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{mail['id']}_{i}"
                    docs.append(
                        Document(
                        page_content=chunk,
                            metadata={
                                "id": mail["id"],
                                "date": mail.get("date", "No Date"),
                                "subject": mail.get("subject", "No Subject"),
                                "sender": mail.get("sender", "Unknown")
                            }
                        )
                    )
                    ids.append(chunk_id)

        return docs,ids

    def process_save_rag(self, docs, ids):
        print(f'ids :{ids}')
        print(f'ids :{docs}')
        if docs:
            self.vectorstore.add_documents(documents=docs, ids=ids)
            print(f"✅ Indexed {len(docs)} chunks (Duplicates overwritten/prevented) ")


    def search(self, question, k=2):
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(question)

        return [doc.page_content for doc in docs]
    
    def get_random_chunk(self, num_chunks=25):
        collection = self.client.get_collection(name="email_rag_nomic")
        results = collection.get(include=['documents'])
        content = results.get('documents', [])
    
        if not content:
         print("⚠️ Database appears to be empty.")
         return []

        if len(content) <= num_chunks:
            return content
        
        return random.sample(content, num_chunks)


    def extract_keywords(self, question):
        # Remove common question words
        stop_words = ["when", "is", "the", "scheduled", "for", "a", "an", "at", "what", "time", "date"]
        words = question.lower().replace("?", "").split()
        # Keep only the unique, important words
        keywords = [word for word in words if word not in stop_words]
        return " ".join(keywords)
    
    def retreive_docs(self, question, k=5):
        keywords = self.extract_keywords(question)

        all_data = self.vectorstore.get()
        keyword_matches = [
            text for text in all_data['documents'] 
            if keywords.lower() in text.lower()
        ]

        if keyword_matches:
            # Use the 4 chunks you found as the context
            context = "\n\n".join(keyword_matches)
            print(f"DEBUG: Using {len(keyword_matches)} keyword matches.")
        else:
            # 2. Fallback to Vector Search if keywords fail
            print("DEBUG: Keyword failed. Falling back to semantic search.")
            docs = self.vectorstore.similarity_search(question, k=5)
            context = "\n\n".join([d.page_content for d in docs])
            print(f'DEBUG : Retreived doc - {context}')
            print('-'*30)
        return context
    
    def retreive_docs_as_list(self, question, k=5):
        """Returns a LIST of strings to satisfy DeepEval requirements."""
        keywords = self.extract_keywords(question)

        # Get the raw data from the vectorstore
        all_data = self.vectorstore.get()
        
        # 1. Keyword search logic
        keyword_matches = [
            text for text in all_data['documents'] 
            if keywords.lower() in text.lower()
        ]

        if keyword_matches:
            # Return only the top k matches as a LIST
            print(f"DEBUG: Using {len(keyword_matches)} keyword matches.")
            return keyword_matches[:k] 
        else:
            # 2. Fallback to Vector Search
            print("DEBUG: Keyword failed. Falling back to semantic search.")
            docs = self.vectorstore.similarity_search(question, k=k)
            
            # Convert Document objects to a LIST of strings
            context_list = [d.page_content for d in docs]
            
            print(f"DEBUG: Retrieved {len(context_list)} docs via semantic search.")
            print('-'*30)
            return context_list

   
    def ask(self, question, k=5 ):
        context = self.retreive_docs(question, k=5)
        current_date = datetime.now().strftime("%A, %B %d, %Y")

        prompt = f"""
       ### TOday's date : {current_date}

        ### CONTEXT FROM SCHOOL EMAILS:
        {context}

        ### INSTRUCTIONS:
        You are a School Information Assistant. Your goal is to provide accurate, specific answers based ONLY on the provided context above. 

        ### CONSTRAINTS:
        1. **Direct Answer:** Provide the answer directly. Include the subject (e.g., "The Badminton tryout is...").
        2. **Exact Matching:** Maintain original formatting for dates and times (e.g., "2/3" or "8:15 a.m.").
        3. **No Meta-Talk:** Do not include phrases like "Based on the context" or "I hope this helps."
        4. **Failure Protocol:** Only if the context is entirely unrelated to the question, state: "I'm sorry, but I couldn't find information regarding [Subject] in the recent school emails."

        ### QUESTION: 
        {question}

        ### ANSWER:
        """

        response = self.llm.invoke(prompt)
        return response.content


    def check_database(self):
        results = self.vectorstore.get()
        
        ids = results.get("ids",[])
        documents = results.get("documents",[])
        metadatas = results.get("metadatas",[])

        for i in range(len(ids)):
            print(f"ID: {ids[i]}")
            print(f"Source: {metadatas[i].get('subject', 'N/A')}")
            print(f"Content Preview: {documents[i][:500]}...") 
            print("-" * 30)

if __name__ == "__main__":
    rag = EmailRAG()
    # rag.check_database()
    # question ='What is the first District Event for robotics?'
   
    # question ='when is the last day for SJCC dual enrollment?'
    # question = "when is coat and blanket drive?"
    # question ="when is SAT School day adminstration"
    # question = "when is the first District Event for robotics?"
    # question = "When is the Digital Safety Presentation scheduled"
    # question = "When are winter tryouts for fall athletes?"
    # question = "When is the first winter tryouts for fall athletes?"
    # question = "When is the Varsity Boys Basketball?"
    #The Varsity Boys Basketball tryout is on Monday, November 3 @ 7:30pm-9:30pm (@ Main Gym).
    # question = "When is the JV/Freshman Boys Basketball?"
    #The JV/Freshman Boys Basketball tryout is on Saturday, November 8 from 9am-12pm (@ Main Gym).
    # question = "When is the last day of course registration for sophomores/rising juniors 2026-27?"
    #The requests for courses will be locked on 3/31/26 at 3:20 pm.
    # question = "When is the wellness week?"

    # question = "when is 11th Grade Parent Night?"
    #11th Grade Parent Night will be held on March 12, 2026, at 6:00 PM in the Cafeteria.

    # question = "when is End-of-Year Chromebook Collection?"
    #End-of-Year Chromebook Collection for Leland High School Students will begin as we approach the end of the 2025–26 school year.
    
    # question = "Any info about new SJUSD new math curriculum?"
    #Savvas Learning Company is the publisher of enVision+ California (Algebra 1, Geometry, Algebra 2), a comprehensive curriculum aligned with the 2023 California Mathematics Framework and the California Common Core State Standards. It provides students with robust problem-solving structures and consistent, standards-aligned instruction necessary to develop mathematical reasoning, procedural fluency, data analysis skills, and deep conceptual understanding.
    
    # question = "When is Badminton tryout?"
    #Badminton tryouts are on Tuesday, February 11 & Wednesday, February 12 from 5:00 PM-8:00 PM and Thursday, February 12 from 6:00 PM-9:00 PM.
    # question = "what is the latest information on badminton season?"
    #The final badminton roster will be posted after school in front of room C-12. If your name is on the roster, please come inside to see me! If you cannot make it to practice next week, notify me via email. Practice Schedule for the week of Feb 16th: Mon 2/16 6:00-8:00 Thurs 2/19 6:00-8:00
    
    # question = "what is the last date for SJCC dual enrollment?"
    #The last day for submission of CCAP forms for the SJCC Psych/Soc. dual enrollment program has been extended to **Feb 23rd** at **3:20 pm** in the CRC.

    # question = "Any upcoming events in March 2026"
    #- March 6 - 7: Half Moon Bay District Event @ Boys & Girls Club of the Coastside in Half Moon Bay
    # - March 28 - 29: Pinnacles District Event @ Hollister High School in 
    # - April 10 - 12: Northern California State Championship @ Cow Palace in Daly City (if qualified)

    # question = "When does the Quixilver team depart for the competition"
    #I'm sorry, but I couldn't find information regarding the departure time of the Quixilver team from the recent school emails.

    # question = "What are the protected characteristics in our school policy?"
        # Ancestry
        # Color
        # Disability
        # Gender
        # Gender Identity
        # Gender Expression
        # Immigration Status
        # Nationality
        # Race or Ethnicity
        # Religion
        # Sex
        # Sexual Orientation
    # question = "When is the Leland Varsity Chargers' dual match against Overfelt?"
    # print(f'question : {question}')
    # question = 'when is Away Game vs. Overfelt Varsity'
   

    # question ='when is Varsity BVAL game'
    #I'm sorry, but I couldn't find information regarding Varsity BVAL game in the recent school emails.
    # question ='Any info  about College and Career Readiness?'
    # print(f'question : {question}')

    # question= 'Why is the  student-led walkout  at Leland High happened'
    # #The student-led walkout at Leland High School was held to express student voice and civic engagement.
    # print(f'question : {question}')

    # question= 'Any info about upcoming Wrestling events '
    # #I'm sorry, but I couldn't find information regarding Wrestling events in the recent school emails.
    # print(f'question : {question}')

    question= 'can you get the badminton practice schedule?'
    # The Badminton tryout schedule for the week of Feb 16th is:

    # Mon 2/16 6:00-8:00
    # Thurs 2/19 6:00-8:00
    print(f'question : {question}')


    print(rag.ask(question))
    # results = rag.vectorstore.similarity_search(question, k=5,filter={"subject": {"$contains": keyword}})

# # 2. Print the results to see if the Robotics info appears
# for i, doc in enumerate(results):
#     print(f"Result {i+1}:")
#     print(f"Subject: {doc.metadata.get('subject')}")
#     print(f"Date: {doc.metadata.get('date')}")
#     print(f"Content Snippet: {doc.page_content[:200]}...")
#     print("-" * 30)

