# 🤖 Smart-RAG: AI-Powered Student Assistance System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Hybrid-green)](https://www.langchain.com/)

[cite_start]An advanced, end-to-end Chatbot solution designed to handle complex institutional queries using **Retrieval-Augmented Generation (RAG)**[cite: 9, 19]. [cite_start]This system bridges the gap between static documents and real-time student support by providing context-aware, human-like responses[cite: 9, 21].

---

## ✨ Key Features

* [cite_start]**Intelligent Knowledge Retrieval:** Leverages **FAISS** for high-speed semantic search across document chunks[cite: 9, 29].
* [cite_start]**Context-Aware Conversations:** Maintains a sophisticated "History-Aware" pipeline that understands follow-up questions by reformulating them based on prior message turns[cite: 44, 59].
* [cite_start]**Multi-Source Data Ingestion:** Automatically processes local **PDFs** and scrapes **live website content** using recursive web crawlers[cite: 10, 39, 75].
* [cite_start]**High Performance:** Powered by the **LLaMA-3.1-8b-instant** model via Groq API, achieving rapid response times[cite: 9, 52].
* [cite_start]**Modern UI:** A sleek, responsive frontend with a typewriter effect, markdown support, and session persistence via UUIDs[cite: 10, 48, 69].

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **LLM Engine** | [cite_start]Groq API (LLaMA-3.1-8b-instant) [cite: 54] |
| **Orchestration** | [cite_start]LangChain [cite: 54] |
| **Vector Store** | [cite_start]FAISS (Facebook AI Similarity Search) [cite: 54] |
| **Embeddings** | [cite_start]HuggingFace `all-MiniLM-L6-v2` [cite: 54] |
| **Backend** | [cite_start]FastAPI (Python) [cite: 54] |
| **Database** | [cite_start]SQLite (Chat History) [cite: 54] |
| **Frontend** | [cite_start]HTML5, Tailwind CSS, Vanilla JS [cite: 54] |

---

## 🏗️ Architecture

[cite_start]The system follows a three-tier architecture to ensure scalability and speed[cite: 35]:

1.  [cite_start]**Ingestion Pipeline:** Files are hashed (MD5) to prevent redundant processing[cite: 38]. [cite_start]Documents are split into 1000-character chunks with a 100-character overlap for optimal context retention[cite: 40].
2.  [cite_start]**RAG Backend:** A FastAPI server handles query contextualization, vector retrieval, and LLM inference[cite: 43, 44].
3.  [cite_start]**Client Interface:** A single-page application (SPA) that communicates via RESTful APIs and stores thread history locally[cite: 47, 49].

---

## 📈 Performance Metrics

[cite_start]The system was evaluated across 250 diverse query categories including admissions, fees, and placements[cite: 86]:

* [cite_start]**Average Precision:** 92.2% [cite: 11, 91]
* [cite_start]**F1-Score:** 0.92 [cite: 11, 113]
* [cite_start]**Average Latency:** 1.2 seconds [cite: 93]

---

## 🚀 Quick Start

### 1. Prerequisites
* Python 3.9 or higher
* A Groq API Key

### 2. Installation
bash
git clone [https://github.com/Vanshika-Malviya/chatbot.git](https://github.com/Vanshika-Malviya/chatbot.git)
cd chatbot
pip install -r requirements.txt

### 3. Run the Application

```bash
uvicorn app:app --reload
```

### 4. Open in Browser

```
http://127.0.0.1:8000
```

---

## 📂 Project Structure

```
chatbot/
│── app.py
│── requirements.txt
│── data/
│── embeddings/
│── templates/
│── static/
```

---

## 🔮 Future Enhancements

- Multi-language support  
- Voice-based interaction  
- Integration with university ERP systems  
- Advanced analytics dashboard  

---

## 🤝 Contributing

Contributions are welcome!  
Feel free to fork the repository and submit a pull request.

---


## 👩‍💻 Authors

- Vanshika Malviya  
