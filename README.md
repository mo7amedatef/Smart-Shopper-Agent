# Smart Shopper Agent 🛒

**An AI-powered e-commerce shopping assistant for the Egyptian market.**

Smart Shopper Agent is an intelligent personal shopping assistant powered by LangChain and LangGraph that helps users find the best products across multiple Egyptian e-commerce platforms. The agent engages in natural conversations in Egyptian Arabic, understands user preferences, and searches across major retailers to provide personalized product recommendations with real-time prices and direct purchase links.

---

## 🎯 Features

- **Conversational AI Assistant**: Natural language interaction in Egyptian Arabic with intelligent clarifying questions
- **Multi-Platform Search**: Real-time product search across Amazon Egypt, B.TECH, and Noon
- **Smart Caching**: Automatic caching of search results to reduce redundant scraping
- **Budget Filtering**: Filter products by price constraints in Egyptian Pounds (EGP)
- **Detailed Specifications**: Extracts processor, RAM, and storage details from listings
- **Direct Purchase URLs**: Returns clickable links for every recommended product
- **Asynchronous Scraping**: Parallel marketplace queries for faster results
- **Chainlit UI**: Streamed chatbot interface for responsive conversations

---

## 🏗️ Architecture Overview

### Ecommerce Tool Execution Flow

![Ecommerce Tool Execution Diagram](Ecommerce%20Tool%20Execution%20Digram.png)

## 💡 How It Works

1. User sends a query through Chainlit chat.
2. The agent uses a LangGraph workflow to manage conversation state.
3. If enough context is available, the agent calls `search_ecommerce_sites` tool.
4. The tool concurrently scrapes Amazon, B.TECH, and Noon and stores results in cache.
5. The agent formats the top products (with prices and URLs) and returns them to the user.

---

## 📁 Project Structure

```
Smart-Shopper-Agent/
├── src/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── scrapers/
│   │   ├── amazon_scraper.py
│   │   ├── btech_scraper.py
│   │   ├── noon_scraper.py
│   │   ├── amazon_spec_scraper.py
│   │   ├── btech_spec_scraper.py
│   │   ├── noon_spec_scraper.py
│   │   └── base_scraper.py
│   ├── database/
│   │   ├── db_manager.py
│   │   └── models.py
│   ├── schemas/
│   │   └── product.py
│   └── ui/
│       └── app.py
├── tests/
│   ├── test_agent_chat.py
│   ├── test_amazon.py
│   ├── test_amazon_full_flow.py
│   ├── test_btech.py
│   ├── test_btech_full_flow.py
│   ├── test_noon.py
│   ├── test_noon_full_flow.py
│   └── test_spec_scraper.py
├── chainlit.md
├── main.py
├── pyproject.toml
├── requirements.txt
├── Ecommerce Tool Execution Digram.png
├── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Groq API key (for LangChain Groq model usage)

### Setup

```bash
git clone https://github.com/mo7amedatef/Smart-Shopper-Agent.git
cd Smart-Shopper-Agent
python -m venv .venv
source .venv/bin/activate
uv sync
```

### Run

```bash
uv run chainlit run src/ui/app.py
```

Then open the Chainlit UI and chat with the agent.

---

## 🧪 Testing

Run tests with:

```bash
uv run pytest -q
```

---

## ⚙️ Configuration

Create `.env` and set your API key values:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## 📌 Notes

- Use short tool query words (e.g., `Dell laptop`) and numeric max price.
- The agent will not hallucinate prices and returns exact product URLs.

---

## 📜 License

MIT License
