# Geo-Contextual Campaign Strategist

This is an end-to-end agentic web application that dynamically generates location-based marketing strategies.It uses Large Language Model and a Model Context Protocol (MCP) server wrapping public REST APIs.

# A Deep Dive
Traditional digital ads often use fixed groups based on demographics.This app does something different by using programmatic advertising that looks at what a person is actually doing at a specific time and place.

It checks real-time environmental factors like temperature, wind, and weather conditions.

It also looks at the area around a person, within a 1 km walk, to see how competitive the area is and what other places are nearby, like offices or cafes.

Then, a local AI assistant uses all this live data to create targeted ad content, decide where to show the ads, and suggest the best way to plan the ad campaign.

## System Architecture & Directory Structure

The repository maintains an isolated, modular layout and provide a clear boundary separation between backend tooling and user presentation layers

```text
geo-campaign-agent/
├── requirements.txt         # dependencies
├── README.md                # documentation
├── mcp_server/              # Microservice API Wrapper
│   └── main.py              # FastAPI implementation
├── agent_backend/           # Stateful LLM Orchestration
│   └── agent.py             # LangGraph & tool boundaries
└── frontend/                # Interactive User Interface
    └── app.py               # Streamlit web app
```
## Setup Instructions

1. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage your dependencies.

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
    
1. **Install Ollama**
   Download from [ollama.com](https://ollama.com/) and pull the Llama 3 model:

   ```bash
   ollama run llama3
   ```
2. Install Python Dependencies

    ```bash
    pip install -r requirements.txt
    ```
3. Start the MCP Server

    ```bash
    python mcp_server/main.py
    ```
4. Start the Frontend Application
Open a new terminal window and run:

    ```bash
    streamlit run frontend/app.py
    ```
---

