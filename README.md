# ✈️ Intelligent Flight Booking Chatbot

> **Graduation Thesis Project**
> Building an Intelligent Chatbot System for Flight Search and Booking using Large Language Models (LLMs), ReAct Agent, Retrieval-Augmented Generation (RAG), and Model Context Protocol (MCP).

---

# 📖 Introduction

The rapid growth of online flight booking platforms has significantly improved accessibility for travelers. However, the overall user experience of existing systems remains fragmented and inefficient when users need to search, compare, analyze, and verify information across multiple airlines simultaneously.

Traditional Online Travel Agency (OTA) platforms still require users to manually:

* fill search forms,
* compare dozens of flight results,
* check baggage policies,
* verify refund conditions,
* and search for promotions across different airline websites.

This process is time-consuming, repetitive, and often causes users to miss important information or promotional offers.

To address these limitations, this project proposes an **Intelligent Flight Booking Chatbot** that allows users to interact entirely through natural language instead of traditional forms and filters.

Rather than acting as a simple FAQ chatbot, the system is designed as an AI-powered conversational assistant capable of:

* understanding complex user intents,
* orchestrating multiple business workflows,
* retrieving real-time flight information,
* analyzing and comparing flights,
* and answering airline policy or promotion-related questions within a single conversation flow.

---

# 🎯 Project Objectives

The project aims to build a conversational AI system capable of:

* Searching and filtering flights using natural language
* Comparing and analyzing flight options across airlines
* Handling multiple intents within a single user message
* Retrieving airline policies and promotions through RAG
* Reducing hallucination by grounding responses on real retrieved data
* Providing a scalable AI architecture using MCP and LangGraph

---

# 🌟 Key Features

## 🔍 Natural Language Flight Search

Users can search flights conversationally without manually filling traditional forms.

Example:

> “Find me the cheapest flight from Hanoi to Phu Quoc tomorrow morning.”

The chatbot automatically extracts:

* departure and destination,
* travel dates,
* passenger information,
* airline preferences,
* seat classes,
* and additional constraints.

---

## ⚖️ Flight Analysis & Comparison

The system supports:

* flight comparison,
* ticket analysis,
* baggage comparison,
* transit evaluation,
* and price optimization.

Users can save flights into a personal comparison cart and ask the chatbot to analyze trade-offs between different options.

---

## 🧠 Multi-Intent Conversational AI

One of the core contributions of the thesis is the ability to process **multiple intents simultaneously within a single conversation turn**.

Example:

> “Find flights from Hanoi to Da Nang this weekend and tell me which airlines currently have baggage promotions.”

Instead of forcing users to ask separate questions step-by-step, the system can:

* search flights,
* retrieve promotions,
* and combine results coherently in one response.

---

## 🔗 ReAct Agent with MCP Architecture

The system is implemented using the **ReAct (Reasoning + Acting)** approach combined with the **Model Context Protocol (MCP)** architecture.

The ReAct Agent:

1. analyzes the user request,
2. determines which tools should be executed,
3. calls external systems through MCP Servers,
4. receives results,
5. continues reasoning if necessary,
6. and finally generates the response.

This architecture separates:

* AI reasoning,
* business logic,
* and external integrations

into independent services for better scalability and maintainability.

---

## 📚 Retrieval-Augmented Generation (RAG)

The chatbot uses RAG to answer questions related to:

* baggage policies,
* refund conditions,
* check-in procedures,
* airline regulations,
* and promotions.

Instead of relying solely on the LLM’s internal knowledge, the system retrieves real airline information from an internal knowledge base before generating responses, helping reduce hallucination and improve factual accuracy.

---

## 🔄 Automated ETL Pipeline

The project includes an automated ETL pipeline for collecting airline knowledge.

The pipeline performs:

* web crawling,
* data cleaning,
* LLM-based normalization,
* document chunking,
* embedding generation,
* and vector storage.

Collected data is stored in PostgreSQL + PGVector for semantic retrieval.

---

# 🏗️ System Architecture

The system follows a microservice-oriented architecture using Docker containers.

Core architectural components include:

* **Frontend (Next.js)**
  Conversational UI and interactive flight display.

* **FastAPI Backend**
  API Gateway and AI orchestration layer.

* **LangGraph ReAct Agent**
  State-based AI workflow management and tool orchestration.

* **Flight MCP Server**
  Handles flight search, filtering, caching, and flight analysis.

* **Knowledge MCP Server**
  Handles RAG retrieval for airline policies and promotions.

* **Redis Cache**
  Stores temporary flight search results to reduce API latency and cost.

* **PostgreSQL + PGVector**
  Stores user data, conversations, and semantic embeddings.

---

# 🛠️ Technology Stack

| Category           | Technologies                                     |
| ------------------ | ------------------------------------------------ |
| Frontend           | Next.js, React, TailwindCSS                      |
| Backend            | FastAPI, Python                                  |
| AI Frameworks      | LangChain, LangGraph                             |
| LLMs               | GPT-4o-mini, Gemini 2.5 Flash, DeepSeek V4 Flash |
| AI Architecture    | ReAct Agent                                      |
| Communication      | MCP (Model Context Protocol)                     |
| Database           | PostgreSQL                                       |
| Vector Storage     | PGVector                                         |
| Cache              | Redis                                            |
| Containerization   | Docker, Docker Compose                           |
| Flight Data Source | Duffel API                                       |

---

# 🚀 Research Contributions

This thesis contributes several important aspects:

* Applying ReAct Agent architecture to flight booking conversations
* Integrating MCP into a real-world AI application
* Supporting multi-intent execution in conversational workflows
* Combining RAG with airline knowledge retrieval
* Building a modular AI microservice architecture
* Evaluating multiple LLM candidates based on:

  * response quality,
  * hallucination rate,
  * latency,
  * and operational cost

---

# 🚀 Installation & Setup

## Prerequisites

Make sure the following tools are installed:

* Docker & Docker Compose
* Node.js >= 20.x
* Python >= 3.10
* Git

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/flight-chatbot.git
cd flight-chatbot
```

---

## 2️⃣ Configure Environment Variables

Create the required `.env` files for each service based on the provided `.env.example` files.

### Backend — `./backend/.env`

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend — `./frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Flight MCP Server — `./mcp-flight/.env`

```env
DUFFEL_API_KEY=your_duffel_api_key
REDIS_HOST=redis
REDIS_PORT=6379
```

### Knowledge MCP Server — `./mcp-knowledge/.env`

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://postgres:postgres@knowledge-db:5432/knowledge_db
```

---

## 3️⃣ Start the System with Docker

Build and start all services:

```bash
docker compose up -d --build
```

This command starts:

* Frontend
* FastAPI Backend
* Flight MCP Server
* Knowledge MCP Server
* PostgreSQL databases
* Redis cache

---

## 4️⃣ Check Running Services

View logs:

```bash
docker compose logs -f
```

Check containers:

```bash
docker compose ps
```
# 👨‍💻 Author

* **Author:** Mễ Quang Huy
* **University:** VNU University of Engineering and Technology
* **Major:** Information Technology
* **Supervisor:** TS. Lê Phê Đô
* **Timeline:** 2025 – 2026

---

# 📄 Thesis Information

This project was developed as a Bachelor's Graduation Thesis titled:

> **“Xây dựng hệ thống Chatbot hỗ trợ tìm kiếm và đặt vé máy bay”**

The thesis focuses on applying Large Language Models, ReAct Agents, MCP architecture, and RAG systems into a real-world conversational flight booking assistant.
