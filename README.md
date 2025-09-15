# Multi-Agent Customer Support Copilot

A **multi-agent AI-powered customer support platform** designed to ingest, classify, and respond to support tickets efficiently. The system combines a **Fast MCP server and client** with a **Streamlit orchestrator**, and leverages **Retrieval Augmented Generation (RAG)** for knowledge-grounded responses.

#Live Demo


## 📑 Table of Contents

- [Overview](#overview)
- [Proposed Agents](#proposed-agents)
- [Architecture](#architecture)
- [Major Design Decisions & Trade-offs](#major-design-decisions--trade-offs)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Future Improvements](#future-improvements)
- [License](#license)

## 📝 Overview

This project provides a **multi-agent AI support system** that enables:

1. **Bulk Ticket Classification Dashboard**: Displays tickets from a sample file with AI-generated classifications (Topic, Sentiment, Priority).
2. **Interactive AI Agent**: Submit new tickets and view both **internal AI analysis** and **final responses**.
3. **Backend Integration**: A **Fast MCP server** manages AI logic and agent orchestration.
4. **Frontend Orchestration**: **Streamlit UI** acts as the orchestrator for displaying analyses and responses in real time.
5. **Voice & Live Chat**: Support for **typed chat** and **voice-based ticket submission** using Whisper STT integration.

**Problem Statement**: Build a core AI pipeline to ingest, classify, and respond to support tickets, demonstrated through a functional dummy helpdesk.

## 🤖 Proposed Agents

### 1. Classification Agent

- **Purpose**: Analyze tickets and assign metadata including topic classification, sentiment analysis, and priority assignment.
- **Tech**: LLaMA via HuggingFace for zero/few-shot classification, Sentence-transformers for sentiment analysis, and rule-based fallback for priority determination.

### 2. RAG Agent

- **Purpose**: Answer knowledge-grounded queries by retrieving relevant information from the knowledge base and generating contextual responses.
- **Tech**: ChromaDB for persistent vector storage, advanced embeddings models, optional reranking for improved accuracy, and LLaMA for response synthesis.

### 3. Routing Agent

- **Purpose**: Handle tickets outside RAG scope by intelligently routing them to appropriate teams or escalation paths.
- **Tech**: Deterministic routing logic based on ticket classification and predefined rules.

### 4. Feedback Agent

- **Purpose**: Log evaluator corrections and user feedback to continuously improve the system's performance.
- **Tech**: Lightweight logging system that stores feedback data for model retraining and performance optimization.

## 🏗 Architecture

<img width="960" height="593" alt="Untitled drawing (9)" src="https://github.com/user-attachments/assets/3a988288-5882-460f-9758-6dfdcc6948d4" />


The system follows a multi-layer architecture with the Streamlit UI orchestrator at the frontend, handling live chat, ticket input, and voice input. This connects to a Fast MCP Server that manages four specialized agents: Classification, RAG, Routing, and Feedback. The backend integrates with data storage, knowledge base, and ChromaDB vector database for comprehensive ticket processing and response generation.

## ⚖ Major Design Decisions & Trade-offs

1. **Multi-Agent Architecture** – Provides modularity and extensibility for different ticket processing needs.
2. **Fast MCP Server** – Ensures lightweight, asynchronous, and modular API exposure.
3. **Streamlit Frontend** – Offers intuitive dashboards and real-time updates via Server-Sent Events.
4. **RAG Integration** – Balances retrieval quality with response latency for optimal user experience.
5. **Modular Design** – Enables easy maintenance, testing, and future enhancements.

## ⚙ Setup & Installation

### Project Structure

The project follows a clean separation between backend and frontend components, with the backend containing all AI agents and the MCP server, while the frontend handles the Streamlit UI orchestration.

### Prerequisites

- Python 3.10 or higher
- Git for cloning the repository

### Local Development Setup

#### 1. Clone the Repository

Clone the repository from your version control system and navigate to the project directory.

#### 2. Backend Setup

Navigate to the backend directory, create a virtual environment, and install the required dependencies. Then start the MCP server which will run on port 8000.

```bash
cd backend
pip install -r requirements.txt
python main_mcp_server.py
```

#### 3. Frontend Setup

In a new terminal, navigate to the frontend directory, install the frontend dependencies, and launch the Streamlit application.

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

#### 4. Access the Application

Once both services are running:
- Frontend UI: [http://localhost:8501](http://localhost:8501)
- Backend API: [http://localhost:8000](http://localhost:8000)

## 🚀 Usage

### Features

- **Bulk Ticket Classification**: Load and analyze sample tickets with automatic topic classification, sentiment analysis, and priority assignment
- **Interactive AI Agent**: Submit new support tickets through the intuitive interface and receive real-time AI analysis and responses
- **Feedback System**: Provide corrections and feedback to improve the system's accuracy over time through the Feedback Agent
- **Knowledge-Based Responses**: Get accurate, sourced responses through the RAG Agent that retrieves information from the knowledge base
- **Smart Routing**: Automatically route tickets that fall outside the knowledge base scope to appropriate teams or escalation paths
- **Voice Input**: Submit support tickets using voice transcription powered by Whisper integration for hands-free interaction

### Getting Started

Navigate to the frontend interface and explore the bulk classification feature with sample tickets. Try submitting new tickets through the interactive interface to see real-time AI processing. Experiment with the voice input functionality for convenient ticket submission. The system provides comprehensive AI analysis including topic classification, sentiment evaluation, and priority assignment for each ticket.

## 🔮 Future Improvements

- **Multi-user Authentication**: Role-based access control and user management system
- **Expanded Knowledge Base**: Integration with broader documentation and knowledge sources beyond current scope
- **Continuous Learning**: Automated model retraining pipeline using collected feedback data
- **Optimized RAG Performance**: Implementation of hybrid search techniques for faster and more accurate retrieval
- **Enhanced Conversational AI**: Advanced chat capabilities with conversation memory and context awareness
- **Platform Integrations**: Seamless connection with popular helpdesk platforms like Zendesk and ServiceNow
- **Advanced Analytics**: Comprehensive reporting dashboard with performance metrics and insights
- **Multi-language Support**: Global customer support with automatic language detection and translation

## 🛠 Tech Stack

The system leverages modern AI and web technologies including Python with FastAPI and MCP Server for the backend, Streamlit for the frontend interface, HuggingFace Transformers and LLaMA for AI processing, ChromaDB for vector storage, and OpenAI Whisper for speech processing capabilities.

## 📄 License

MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

If you have any questions or run into issues, please open an issue on GitHub or contact the development team.

