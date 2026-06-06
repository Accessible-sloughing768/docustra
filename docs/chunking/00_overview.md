# Chunking Strategies — Overview

Chunking is the process of splitting documents into smaller pieces before embedding and storing them in Qdrant. The chunking strategy you choose directly affects retrieval quality — wrong chunk boundaries mean relevant information gets split across chunks, missed by similarity search, or returned without enough context for the LLM to answer correctly.

Docustra supports **10 chunking strategies** selectable per ingestion, from the sidebar in the UI or via the API.

---

## Quick Comparison

| Strategy | Speed | Chunk Quality | LLM Required | Best For |
|---|---|---|---|---|
| [Recursive](01_recursive.md) | ⚡ Fast | Good | No | General purpose (default) |
| [Character](02_character.md) | ⚡ Fast | Basic | No | Structured paragraph text |
| [Token](03_token.md) | ⚡ Fast | Good | No | LLM context window compliance |
| [Sentence Transformers](04_sentence_transformers.md) | ⚡ Fast | Good | No | Preventing embedding truncation |
| [Semantic](05_semantic.md) | 🐢 Slow* | Excellent | No** | Technical docs, topic shifts |
| [Sentence Window](06_sentence_window.md) | ⚡ Fast | Excellent | No | Dense text, precise retrieval |
| [Markdown](07_markdown.md) | ⚡ Fast | Very Good | No | Markdown docs, wikis, READMEs |
| [HTML](08_html.md) | ⚡ Fast | Very Good | No | Web pages, HTML reports |
| [Parent-Child](09_parent_child.md) | ⚡ Fast | Excellent | No | Long documents, best accuracy |
| [Hypothetical Questions](10_hypothetical_questions.md) | 🐢 Slow | Excellent | Yes 🤖 | Q&A, conversational docs |

*Slow because it embeds every sentence to detect topic changes
**Uses the embedding model, not the LLM

---

## How to Select a Strategy

**Via UI:** Sidebar → Chunking Strategy dropdown → select → Ingest

**Via API:**
```bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "file=@document.pdf" \
  -F "chunking_strategy=semantic"
```

**List all available strategies:**
```bash
curl http://localhost:8000/ingest/strategies
```

---

## Decision Guide

```
What type of document are you ingesting?
│
├── Markdown file (.md) → Markdown strategy
├── HTML / web page     → HTML strategy
├── Source code         → Recursive (code mode)
│
└── PDF / plain text
      │
      ├── Is it FAQ-style / Q&A format?
      │     └── YES → Hypothetical Questions
      │
      ├── Is dense technical text with long passages?
      │     └── YES → Sentence Window or Parent-Child
      │
      ├── Do you need maximum retrieval accuracy?
      │     └── YES → Parent-Child
      │
      ├── Does topic change frequently within sections?
      │     └── YES → Semantic
      │
      ├── Using GPT-4 / Claude with strict token limits?
      │     └── YES → Token
      │
      └── General purpose
            └── Recursive (default)
```

---

## Chunk Size Configuration

All non-LLM strategies respect the `CHUNK_SIZE` and `CHUNK_OVERLAP` settings in `.env`:

```env
CHUNK_SIZE=512     # characters (or tokens for Token strategy)
CHUNK_OVERLAP=64   # overlap between consecutive chunks
```

**Tuning guidance:**

| Document type | Recommended CHUNK_SIZE |
|---|---|
| Dense technical (e.g. research papers) | 1024 |
| General enterprise docs | 512 (default) |
| FAQ / short-answer docs | 256 |
| Legal / regulatory (long clauses) | 1024–2048 |

---

## What Happens After Chunking

Every chunk becomes a `Document` object with:
- `page_content` — the text that gets embedded
- `metadata` — source file, page number, chunk type, strategy-specific fields

These are then:
1. **Embedded** by `sentence-transformers/all-MiniLM-L6-v2` (locally on MPS)
2. **Stored** in Qdrant as a 384-dimensional vector + payload
3. **Retrieved** at query time via cosine similarity search

---

## Detailed Documentation

| # | Strategy | Doc |
|---|---|---|
| 1 | Recursive Character | [01_recursive.md](01_recursive.md) |
| 2 | Character | [02_character.md](02_character.md) |
| 3 | Token | [03_token.md](03_token.md) |
| 4 | Sentence Transformers Token | [04_sentence_transformers.md](04_sentence_transformers.md) |
| 5 | Semantic | [05_semantic.md](05_semantic.md) |
| 6 | Sentence Window | [06_sentence_window.md](06_sentence_window.md) |
| 7 | Markdown | [07_markdown.md](07_markdown.md) |
| 8 | HTML | [08_html.md](08_html.md) |
| 9 | Parent-Child | [09_parent_child.md](09_parent_child.md) |
| 10 | Hypothetical Questions | [10_hypothetical_questions.md](10_hypothetical_questions.md) |
