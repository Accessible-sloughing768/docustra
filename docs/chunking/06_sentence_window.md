# Sentence Window Chunker

**Strategy ID:** `sentence_window` | **LLM Required:** No

## What It Does

Splits text into **individual sentences** for indexing, but stores a **window of surrounding sentences** in the metadata. This solves the classic RAG dilemma:

- **Small chunks** → precise vector retrieval (the right sentence is found)
- **Large chunks** → rich context for the LLM (enough text to answer properly)

Sentence Window gives you **both** simultaneously.

---

## The Core Concept

```
Text:
S1: "Qdrant is a vector database built for production."
S2: "It supports HNSW indexing for fast ANN search."
S3: "The payload filtering system allows pre-filtering before ANN."
S4: "This reduces the search space and improves latency."
S5: "Qdrant also supports sparse vectors for hybrid search."

window_size = 2

What gets INDEXED (embedded as vector):
  Each sentence individually → 5 small, precise vectors

What gets STORED in metadata (returned to LLM):
  Sentence S3 + window:
    window_context = "S2 + S3 + S4" (±2 sentences around S3)
    = "It supports HNSW indexing... payload filtering... reduces search space"

When user asks: "How does Qdrant's filtering work?"
  → Vector search finds S3 (exact match, high precision)
  → LLM receives window (S2 + S3 + S4) for context
  → Answer includes context about HNSW, filtering, AND latency impact
```

---

## How Retrieval Uses Window Context

The `window_context` field in metadata contains the full surrounding text. RAG strategies that are context-aware (or that you configure) can use `parent_content` / `window_context` instead of `page_content` when building the answer context:

```python
# In your retrieval strategy, use window_context if available:
context = doc.metadata.get("window_context") or doc.page_content
```

This is handled automatically in Docustra's retrieval layer when the `sentence_window` strategy is detected.

---

## Configuration

```json
{
  "chunking_strategy": "sentence_window",
  "chunking_params": {
    "window_size": 3
  }
}
```

| window_size | Context sentences | Best for |
|---|---|---|
| 1 | ±1 sentence (3 total) | Very dense text, short answers |
| 2 | ±2 sentences (5 total) | Standard technical docs |
| 3 | ±3 sentences (7 total) | Complex reasoning, long context (default) |
| 5 | ±5 sentences (11 total) | Narrative documents, reports |

---

## Metadata Produced

```python
{
  "source": "vector-databases-guide.pdf",
  "page": 12,
  "type": "text",
  "window_context": "HNSW index... payload filtering... reduces latency...",
  "sentence_index": 42,
  "window_size": 3,
  "chunking": "sentence_window"
}
```

---

## Chunk Count Impact

Sentence Window produces **many more chunks** than other strategies:

```
Document: 73 recursive chunks → ~800 sentences → 800 vectors in Qdrant

With window_size=3:
  Each sentence = 1 vector
  Each vector's metadata contains ±3 sentences context

Qdrant storage: ~5-10× more vectors than recursive
Retrieval: more precise
```

Consider this trade-off for large documents.

---

## Demo Example

**Query:** "What is payload filtering in Qdrant?"

**With Recursive chunking (512 chars):**
```
Retrieved chunk (512 chars):
"Qdrant is a vector database. It supports HNSW. The payload filtering
system allows pre-filtering before ANN. This reduces search space.
Qdrant also supports sparse vectors..."

The answer about filtering is buried in a mix of unrelated facts.
```

**With Sentence Window (window=3):**
```
Indexed sentence: "The payload filtering system allows pre-filtering before ANN."
Retrieved window_context:
"It supports HNSW indexing for fast ANN search.       [S2 — context]
 The payload filtering system allows pre-filtering.   [S3 — exact match]
 This reduces the search space and improves latency."  [S4 — consequence]

LLM receives focused, relevant context with cause + effect.
```

---

## When to Use

✅ **Best for:**
- Dense technical documentation (every sentence matters)
- Documents where single sentences contain key facts (specs, definitions)
- When you want surgical precision in retrieval + enough context for answers
- FAQ-style documents where Q&A pairs are in adjacent sentences

❌ **Avoid when:**
- Document is very large (produces too many vectors — use `parent_child` instead)
- Sentences are very long (academic writing, legal text — window gives too much overlap)
- Low storage budget in Qdrant

---

## Comparison with Parent-Child

| | Sentence Window | Parent-Child |
|---|---|---|
| Indexed unit | Individual sentence | Small child chunk (256 chars) |
| Context unit | ±N surrounding sentences | Full parent chunk (1024 chars) |
| Vector count | Very high (1 per sentence) | Moderate (1 per child chunk) |
| Best for | Short fact-dense docs | Long structured docs |
