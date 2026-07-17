# AI Financial Crime Investigation Platform

<p align="center">
  <strong>An Enterprise-Grade, AI-Powered Anti-Money Laundering (AML) & Financial Crime Investigation System.</strong>
</p>

---

## 📖 Project Overview

The **AI Financial Crime Investigation Platform** is an advanced, production-grade system designed for banking and financial institutions. Going significantly beyond traditional binary fraud detection, this platform leverages modern Artificial Intelligence, Machine Learning, and Graph Database technologies to autonomously detect, investigate, and report suspicious financial activities.

### Core Capabilities:
- **Autonomous Detection**: Identifies suspicious financial transactions and typologies (e.g., Structuring, Circular Fund Movements, Mule Networks).
- **Knowledge Graph Analysis**: Analyzes deep relationships between customers, accounts, and organizations using Neo4j.
- **Explainable AI (XAI)**: Generates explainable risk scores and human-readable investigation summaries using Large Language Models (LLMs).
- **Automated Investigation**: Employs Multi-Agent AI (RAG) to retrieve regulatory knowledge and automatically draft Suspicious Activity Reports (SARs).

---

## 🏗️ System Architecture

This platform is built using a modern, scalable, and modular tech stack to ensure enterprise readiness and maintainability.

### Tech Stack
- **Backend**: FastAPI (Python), utilizing clean architecture and dependency injection.
- **Relational Database**: PostgreSQL (with `pgvector`) for storing core banking data (Customers, Accounts, Transactions) and ML embeddings.
- **Graph Database**: Neo4j for mapping complex financial entity relationships and detecting obfuscated money laundering rings.
- **Caching & Messaging**: Redis for high-performance caching and background task brokering.
- **AI & LLM Integration**: Gemini via LangChain, keeping the LLM layer provider-agnostic.
- **Infrastructure**: Fully containerized using Docker and Docker Compose.

---

## ⚙️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/rohith-chitturi/AI-Financial-Crime-Investigation-Platform.git
   cd AI-Financial-Crime-Investigation-Platform
   ```

2. **Environment Configuration:**
   Copy the example environment file and configure your credentials.
   ```bash
   cp .env.example .env
   ```
   *(Note: Never commit `.env` files containing real API keys or database credentials to version control.)*

3. **Start Infrastructure Services:**
   Launch PostgreSQL, Neo4j, and Redis using Docker Compose.
   ```bash
   docker-compose up -d
   ```

4. **Initialize Backend Environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. **Run Database Migrations:**
   Apply Alembic migrations to set up the PostgreSQL schemas.
   ```bash
   alembic upgrade head
   ```

6. **Generate Synthetic Data:**
   Seed the database with a realistic, simulated banking ecosystem (including injected AML typologies).
   ```bash
   python scripts/generate_data.py
   ```

7. **Run the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be accessible at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

---

## 🛡️ Security & AI Safety

- **Data Privacy**: Ground-truth labels for suspicious transactions are strictly isolated from production investigation APIs and LLM context windows to prevent data leakage during AI evaluation.
- **Report Generation**: All AI-generated Suspicious Activity Reports (SARs) are strictly labeled as `DRAFT` and require human analyst review before submission.
- **Access Control**: Role-Based Access Control (RBAC) is implemented via JWT authentication to restrict access to sensitive financial data.

---

## ⚖️ Legal Disclaimer & License

**Disclaimer:** 
This software is provided for educational, research, and demonstration purposes only. It is not intended for use in live production environments handling real financial data without rigorous compliance auditing, security testing, and regulatory approval. The creators and contributors are not liable for any misuse, data breaches, or regulatory penalties resulting from the deployment of this platform.

**Copyright © 2026 Rohith Chitturi (CH ROHITH). All Rights Reserved.**

*This project is proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited without the express written consent of the author.*
