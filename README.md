# finquagent

finquagent is an intelligent document understanding system that combines advanced document extraction, agent-based reasoning, and Retrieval-Augmented Generation (RAG) using Qdrant to analyze and interact with structured and unstructured financial documents.

It is specifically designed to automate insights from documents like bank statements, invoices, PDF reports, and more — enabling accurate, user-specific queries and contextual responses using Large Language Models and vector similarity search.

## 🚀 Features
🧠 Agent-based Architecture for modular analysis & actions

📑 Document Parsing & Splitting using LangChain tools

🧭 Qdrant-powered RAG for semantic search and document-specific question answering

💬 Query Engine to fetch relevant document chunks per user and query

📂 Supports multi-user vector storage with contextual memory

🔐 API-key secured integration with OpenAI for embedding generation

## 🛠️ Tech Stack

Tool/Library	                Purpose
Python	                     Core programming language
LangChain	                   Document loaders & text splitting
Qdrant	                     Vector database backend for semantic search
OpenAI	                     Embedding generation (text-embedding-3-small)
dotenv	                     Manage environment variables
uuid	                       Unique ID generation for vector entries

### make sure to have .env file in your root directory and includes these apis
OPENAI_API_KEY=your-openai-api-key
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_HOST=http://localhost:6333
QDRANT_COLLECTION_NAME=your_collection_name


## 📥 Installation Guide
bash
Copy
Edit
### Clone the repo
git clone https://github.com/your-username/finquagent.git
cd finquagent

### Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### Install dependencies
pip install -r requirements.txt


# 🤝 Contributing
Pull requests are welcome. For significant changes, please open an issue first to discuss what you would like to change.

# 🧠 Credits
LangChain

Qdrant

OpenAI Embeddings

