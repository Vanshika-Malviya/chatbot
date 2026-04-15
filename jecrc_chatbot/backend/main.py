from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache

# Setup in-memory LLM caching
set_llm_cache(InMemoryCache())

load_dotenv()

app = FastAPI(title="JECRC Support Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONSTANTS & PATHS (Fixed for nested folder structure) ---
# Moves up from 'backend' to the 'jecrc' root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
FAISS_INDEX_PATH = os.path.join(DB_DIR, "faiss_index")
SQLITE_URL = f"sqlite:///{os.path.join(DB_DIR, 'chat_history.db')}"

os.makedirs(DB_DIR, exist_ok=True)

class LimitedSQLChatMessageHistory(SQLChatMessageHistory):
    @property
    def messages(self):
        msgs = super().messages
        return msgs[-6:] if len(msgs) > 6 else msgs

# Global AI states
vectorstore = None
retriever = None
llm = None
conversational_rag_chain = None

@app.on_event("startup")
def startup_event():
    global vectorstore, retriever, llm, conversational_rag_chain
    
    print(f"--- STARTUP: SEARCHING FOR DATABASE ---")
    print(f"Looking in: {FAISS_INDEX_PATH}")
    
    if not os.path.exists(FAISS_INDEX_PATH):
        print("ERROR: FAISS index folder NOT FOUND. Run ingest_data.py first.")
        return

    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",
            temperature=0.2
        )

        # Contextualize question logic
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question, "
            "formulate a standalone question which can be understood without the history."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

        # PERSONA: Academic Counselor focused on Website + PDF Data
        system_prompt = (
    "You are the official JECRC Foundation Assistant. "
    "Use the following context to answer the user's question accurately. "
    "Context: {context}\n\n"
    "RULES:\n"
    "1. Answer directly and professionally.\n"
    "2. Use bullet points for lists.\n"
    "3. Do not include any signatures, symbols, or conversational filler like 'Hey there'.\n"
    "4. If a source URL is in the context, provide it at the end."
)

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        def get_session_history(session_id: str):
            return LimitedSQLChatMessageHistory(session_id=session_id, connection_string=SQLITE_URL)

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        print("Backend loaded successfully. DB Linked.")

    except Exception as e:
        print(f"Startup Error: {e}")

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    if not conversational_rag_chain:
        raise HTTPException(status_code=503, detail="AI engine not initialized. Check server logs.")
    try:
        response = conversational_rag_chain.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}}
        )
        return {"response": response["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
def get_history(session_id: str):
    try:
        history = SQLChatMessageHistory(session_id=session_id, connection_string=SQLITE_URL)
        messages = [{"role": "user" if m.type == "human" else "assistant", "content": m.content} for m in history.messages]
        return {"messages": messages[-10:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))