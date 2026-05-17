# BOB PROMPT: Generate Architecture Diagram (Mermaid) for BB84 QKD Educational Interface

## Role & Context

You are IBM Bob, my expert AI development partner. I have built **CryptoLab: BB84** – a full‑stack quantum key distribution educational tool with:

- Streamlit frontend (Simulation, Eve Game, Wizard, Bob Modes, Cross‑Layer, Cloud, Chat API tabs)
- Multiple simulation backends (Qiskit Aer, vectorised NumPy, density matrix)
- Project Bob performance observability (collectors, SLA monitors, root cause analyzers, fix recommenders, ROI projectors)
- Cloud infrastructure monitoring (CPU, memory, network, cost, auto‑scaling policies)
- Chat API performance tracking (latency, tokens, error rates)
- REST API (FastAPI) exposing all capabilities

I need a **clear, professional architecture diagram** that shows:
- All major components and their relationships
- Data flow (user → frontend → simulation → collectors → analysis → recommendations)
- External dependencies (IBM Qiskit, Streamlit, Plotly, etc.)
- Optional integrations (OpenAI API, cloud providers, GPU)

## Your Task

Generate a **Mermaid diagram** (```mermaid) that describes the system architecture. Use appropriate node shapes, subgraphs, and arrows. Include at least:

1. **User / Browser** – entry point
2. **Streamlit Frontend** – with its main tabs (Simulation, Eve Game, Wizard, Bob Modes, Cross‑Layer, Cloud, Chat API)
3. **Simulation Engines** – three boxes: Qiskit Aer, Vectorised (NumPy), Density Matrix
4. **Project Bob Core** – subgraph containing: Performance Collector, SLA Monitor, Root Cause Analyzer, Fix Recommender, Fix Simulator, ROI Projector
5. **Cloud Monitor** – subgraph: Cloud Collector, Cloud SLA Monitor, Cloud Fix Recommender, Auto‑Scaling Policy
6. **Chat API Monitor** – subgraph: Chat Collector, Chat SLA Monitor, Chat Fix Recommender, Capacity Planner
7. **External APIs** – OpenAI (optional), Simulated Chat API
8. **Data Storage** – session state, cache (Redis or in‑memory), benchmark results (CSV/JSON)
9. **REST API (FastAPI)** – optional, shown as a separate entry point for programmatic access

## Format

- Output only the Mermaid diagram inside a markdown code block.
- Use `flowchart TD` (top‑down) or `graph TD`.
- Add descriptive labels and comments using `%%`.
- Ensure the diagram is readable (not too dense; group related components in subgraphs).

## Example Structure

```mermaid
flowchart TD
    User[User / Browser] --> Frontend[Streamlit Frontend]
    Frontend --> Tabs
    subgraph Tabs
        SimTab[Simulation Tab]
        EveTab[Eve Game Tab]
        BobTab[Bob Modes Tab]
    end
    SimTab --> SimEngines
    subgraph SimEngines
        Qiskit[Qiskit Aer]
        Vectorised[NumPy Vectorised]
        Density[Density Matrix]
    end
    SimEngines --> BobCore
    subgraph BobCore
        Collector[Performance Collector]
        Monitor[SLA Monitor]
        RCA[Root Cause Analyzer]
        ...
    end
    ...
```

## Begin

Generate the architecture diagram now.

---

## GENERATED ARCHITECTURE DIAGRAM

```mermaid
flowchart TD
    %% Entry Points
    User([User / Browser]) --> StreamlitUI[Streamlit Frontend<br/>app/streamlit_app.py]
    Developer([Developer / API Client]) --> FastAPI[FastAPI REST Endpoint<br/>chat.py]
    
    %% Streamlit Frontend Tabs
    StreamlitUI --> Tabs
    subgraph Tabs[" Frontend Tabs "]
        PlaygroundTab[🎮 Playground<br/>Interactive Simulation]
        WizardTab[📚 Step-by-Step<br/>Guided Learning]
        EveTab[🕵️ Eve Mode<br/>Attack Scenarios]
        AnalyticsTab[📊 Security Analytics<br/>QBER Heatmaps]
        BobCopilotTab[🤖 Bob Copilot<br/>AI Assistant]
        BuilderTab[🔧 Builder Notes<br/>Development Guide]
    end
    
    %% Core Protocol Layer
    Tabs --> ProtocolCore
    subgraph ProtocolCore[" BB84 Protocol Core "]
        BB84Sim[bb84.py<br/>Core Simulator]
        Models[models.py<br/>Data Structures]
        Analytics[analytics.py<br/>QBER Analysis]
    end
    
    %% Simulation Backends
    BB84Sim --> SimEngines
    subgraph SimEngines[" Simulation Engines "]
        Analytical[Analytical Mode<br/>Fast NumPy]
        QiskitBackend[Qiskit Aer<br/>Circuit Validation]
        DensityMatrix[Density Matrix<br/>Noise Modeling]
    end
    
    %% Educational Layer
    ProtocolCore --> Education
    subgraph Education[" Educational Components "]
        EduModule[education.py<br/>Glossary & Walkthroughs]
        Reporting[reporting.py<br/>Export Reports]
        CLI[cli.py<br/>Command Line Interface]
    end
    
    %% AI & Chat Integration
    BobCopilotTab --> AILayer
    FastAPI --> AILayer
    subgraph AILayer[" AI Integration Layer "]
        WatsonxClient[watsonx_client.py<br/>IBM watsonx.ai]
        ChatEndpoint[chat.py<br/>FastAPI Chat Service]
        LocalFallback[Local Fallback<br/>Safe Mode]
    end
    
    %% External AI Services
    WatsonxClient -.->|Optional| WatsonxAPI[IBM watsonx.ai<br/>Granite Models]
    ChatEndpoint -.->|Optional| OpenAI[OpenAI API<br/>GPT Models]
    ChatEndpoint -.->|Simulation Mode| SimulatedChat[Simulated Responses<br/>Dev/Test Mode]
    
    %% Data & Storage
    ProtocolCore --> DataLayer
    Education --> DataLayer
    subgraph DataLayer[" Data & Storage "]
        SessionState[Streamlit Session State<br/>In-Memory Cache]
        FileExports[File Exports<br/>JSON/Markdown/CSV]
        BobSessions[bob-sessions/<br/>Bob IDE Reports]
    end
    
    %% Testing & Quality
    subgraph Testing[" Testing & Quality "]
        PyTest[tests/test_bb84.py<br/>Unit Tests]
        ReportingTests[tests/test_reporting_cli.py<br/>CLI Tests]
    end
    
    Testing -.->|Validates| ProtocolCore
    Testing -.->|Validates| Education
    
    %% External Dependencies
    subgraph ExtDeps[" External Dependencies "]
        Qiskit[IBM Qiskit<br/>Quantum Framework]
        Streamlit[Streamlit<br/>Web Framework]
        Plotly[Plotly<br/>Visualizations]
        NumPy[NumPy<br/>Numerical Computing]
        Pandas[Pandas<br/>Data Analysis]
    end
    
    SimEngines --> Qiskit
    StreamlitUI --> Streamlit
    StreamlitUI --> Plotly
    SimEngines --> NumPy
    Analytics --> Pandas
    
    %% Styling
    classDef userNode fill:#0f62fe,stroke:#001d6c,color:#fff,stroke-width:3px
    classDef coreNode fill:#0353e9,stroke:#001d6c,color:#fff,stroke-width:2px
    classDef aiNode fill:#8a3ffc,stroke:#6929c4,color:#fff,stroke-width:2px
    classDef dataNode fill:#198038,stroke:#0e6027,color:#fff,stroke-width:2px
    classDef extNode fill:#f1c21b,stroke:#d2a106,color:#000,stroke-width:2px
    classDef testNode fill:#da1e28,stroke:#a2191f,color:#fff,stroke-width:2px
    
    class User,Developer userNode
    class BB84Sim,Models,Analytics,Analytical,QiskitBackend,DensityMatrix coreNode
    class WatsonxClient,ChatEndpoint,LocalFallback,WatsonxAPI,OpenAI,SimulatedChat aiNode
    class SessionState,FileExports,BobSessions dataNode
    class Qiskit,Streamlit,Plotly,NumPy,Pandas extNode
    class PyTest,ReportingTests testNode
```

## Diagram Explanation

### Architecture Layers

1. **Entry Points**
   - Browser users interact via Streamlit UI
   - Developers/scripts access via FastAPI REST endpoint

2. **Frontend Layer** (Streamlit)
   - 6 main tabs for different use cases
   - Playground for quick experiments
   - Wizard for guided learning
   - Eve Mode for security testing
   - Analytics for QBER visualization
   - Bob Copilot for AI assistance
   - Builder Notes for developers

3. **Protocol Core**
   - `bb84.py`: Main simulation engine
   - `models.py`: Typed data structures (RunConfig, ProtocolRun)
   - `analytics.py`: Parameter sweeps and QBER analysis

4. **Simulation Engines**
   - Analytical: Fast NumPy-based calculations
   - Qiskit Aer: Circuit-level quantum simulation
   - Density Matrix: Advanced noise modeling

5. **Educational Components**
   - Glossary and walkthrough content
   - Report generation (JSON/Markdown)
   - CLI for scripted simulations

6. **AI Integration**
   - IBM watsonx.ai client (optional)
   - FastAPI chat endpoint with OpenAI support
   - Local fallback for offline/demo mode

7. **Data Storage**
   - Session state for UI persistence
   - File exports for reports
   - Bob sessions folder for IDE reports

8. **Testing**
   - Unit tests for protocol correctness
   - CLI and reporting tests

9. **External Dependencies**
   - Qiskit for quantum simulation
   - Streamlit for web UI
   - Plotly for interactive charts
   - NumPy/Pandas for data processing

### Data Flow

1. User configures simulation parameters in Streamlit sidebar
2. Frontend calls BB84 protocol core with RunConfig
3. Core selects appropriate simulation engine
4. Engine executes BB84 protocol (Alice → Eve → Bob → Sifting → QBER)
5. Results flow back through analytics layer
6. Frontend renders visualizations and metrics
7. Optional: Bob Copilot provides AI explanations via watsonx.ai
8. Optional: Reports exported to files or API responses

### Key Design Principles

- **Separation of Concerns**: Protocol logic independent from UI
- **Extensibility**: Easy to add new simulation backends
- **Optional AI**: Works with or without external AI services
- **Developer-Friendly**: CLI, tests, and clear module boundaries
- **Educational Focus**: Multiple learning paths (playground, wizard, analytics)

This architecture supports the IBM Bob Hackathon goals by providing:
- Clear extension points for Bob-assisted development
- Modular design that Bob can understand and modify
- Multiple interfaces (UI, CLI, API) for different use cases
- Strong foundation for adding features like Qiskit validation mode