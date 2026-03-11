```mermaid
graph LR
    subgraph "1. Daily Sync (Background)"
    A[Gmail API] -->|Fetch| B[EmailRAG: Process/Save]
    B --> C[(ChromaDB)]
    C -.->|Track Date| D[last_sync.txt]
    end

    subgraph "2. Live Chat (User Flow)"
    E[Gradio UI] --> F[Chatbot]
    C -->|Context| F
    F -->|Ollama| G[Llama 3.1]
    end

    subgraph "3. Development (Independent)"
    G -.-> H{DeepEval}
    I[Golden Dataset] --> H
    H -- "Refine Logic" --> B
    end