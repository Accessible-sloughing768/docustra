# Docustra — UI Screenshots

This directory contains screenshots of the Docustra Streamlit UI for GitHub portfolio showcase.

## How to Add Screenshots

Launch the UI and take screenshots:

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# Start API
uv run docustra-api

# Start Streamlit
uv run streamlit run src/docustra/ui/app.py
# Opens at http://localhost:8501
```

Then take screenshots of each tab and save them here as `.png` files.

---

## Recommended Screenshots

| Filename | What to capture |
|---|---|
| `01_ingest_tab.png` | Document Intelligence tab — PDF uploaded, strategy selected, params visible |
| `02_ingest_parent_child.png` | Parent-Child strategy selected with parent/child size params shown |
| `03_ingest_semantic.png` | Semantic strategy with breakpoint dropdown |
| `04_query_adaptive.png` | Query tab — question answered via Adaptive RAG with sources |
| `05_query_self_rag.png` | Self-RAG response showing [Retrieve][Relevant][Supported] tokens in Reasoning |
| `06_query_graph_rag.png` | Graph RAG response showing entity relationships in reasoning |
| `07_system_dashboard.png` | System Dashboard — all services green, Qdrant stats |
| `08_qdrant_dashboard.png` | Qdrant web UI at localhost:6333/dashboard showing stored vectors |
| `09_phoenix_traces.png` | Arize Phoenix trace view at localhost:6006 showing RAG chain steps |

---

## Screenshot Tips

- Use **1440×900** or **1920×1080** window for consistent sizing
- Use browser zoom at **100%**
- For Streamlit, use **Light theme** (Settings → Theme → Light)
- Capture the full browser window including the tab bar for context

---

## Adding to README

Once screenshots are taken, reference them in the main README:

```markdown
## Screenshots

### Document Intelligence Tab
![Ingest Tab](docs/screenshots/01_ingest_tab.png)

### RAG Query Tab  
![Query Tab](docs/screenshots/04_query_adaptive.png)

### System Dashboard
![Dashboard](docs/screenshots/07_system_dashboard.png)
```
