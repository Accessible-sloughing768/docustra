# Markdown Header Text Splitter

**Strategy ID:** `markdown` | **LLM Required:** No

## What It Does

Splits Markdown documents on **header boundaries** (`#`, `##`, `###`, `####`) and preserves the **full header hierarchy** as metadata on every chunk. Each chunk knows which section of the document it belongs to.

---

## Why This Matters for RAG

Standard chunkers treat Markdown as plain text. A 512-char chunk might be:

```
Recursive chunk:
"## Indexing Algorithms
HNSW (Hierarchical Navigable Small World) is the de-facto standard...
...and IVF (Inverted File Index) divides the vector space...

## Filtering
Qdrant's payload filtering enables..."
```

This chunk crosses a section boundary. A question about "filtering" retrieves this chunk — but the top half is about indexing, not filtering.

**Markdown chunking:**
```
Chunk 1: {h2: "Indexing Algorithms"}
  "HNSW (Hierarchical Navigable Small World) is the de-facto standard..."

Chunk 2: {h2: "Filtering"}
  "Qdrant's payload filtering enables pre-filtering of the vector space..."
```

Each chunk is topically pure AND carries its section context.

---

## How It Works

```
Input Markdown:
# Vector Databases Guide
## Section 1: Core Concepts
### 1.1 What is a Vector?
A vector is a mathematical object...

### 1.2 Embeddings
Embeddings are dense vector representations...

## Section 2: Indexing
### 2.1 HNSW
HNSW builds a layered graph...

Split on headers → sections:
┌─────────────────────────────────────────┐
│ h1: "Vector Databases Guide"            │
│ h2: "Section 1: Core Concepts"          │
│ h3: "1.1 What is a Vector?"             │
│ Content: "A vector is a mathematical..."│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ h1: "Vector Databases Guide"            │
│ h2: "Section 1: Core Concepts"          │
│ h3: "1.2 Embeddings"                    │
│ Content: "Embeddings are dense..."      │
└─────────────────────────────────────────┘
...etc.
```

If a section is still too large, a secondary `RecursiveCharacterTextSplitter` further divides it while preserving the header metadata.

---

## Configuration

```json
{
  "chunking_strategy": "markdown",
  "chunking_params": {
    "chunk_size": 1024
  }
}
```

Default headers: `#` (h1), `##` (h2), `###` (h3), `####` (h4)

---

## Metadata Produced

```python
{
  "source": "readme.pdf",
  "page": 1,
  "type": "text",
  "h1": "Vector Databases Guide",
  "h2": "Section 2: Indexing",
  "h3": "2.1 HNSW",
  "chunking": "markdown"
}
```

The header metadata can be used for **filtered retrieval** in Qdrant:
```python
# Retrieve only from Section 2: Indexing
results = vector_store.similarity_search(
    query,
    filter={"must": [{"key": "h2", "match": {"value": "Section 2: Indexing"}}]}
)
```

---

## Demo Example

**Document:** This project's own `ARCHITECTURE.md`

```markdown
# Docustra — Architecture Deep Dive

## RAG Pattern Implementations

### 1. Adaptive RAG
**Problem solved:** Not every query needs deep retrieval...

### 2. Agentic RAG
**Problem solved:** Multi-step queries that require iterative discovery...
```

**After Markdown chunking:**
```
Chunk 1:
  metadata: {h1: "Docustra — Architecture Deep Dive",
             h2: "RAG Pattern Implementations",
             h3: "1. Adaptive RAG"}
  content:  "Problem solved: Not every query needs deep retrieval..."

Chunk 2:
  metadata: {h1: "Docustra — Architecture Deep Dive",
             h2: "RAG Pattern Implementations",
             h3: "2. Agentic RAG"}
  content:  "Problem solved: Multi-step queries that require..."
```

Query "How does Adaptive RAG work?" now retrieves Chunk 1 with its full section context in metadata.

---

## When to Use

✅ **Best for:**
- READMEs, wikis, and technical documentation in Markdown
- Developer docs (API references, guides)
- Any document where headers define semantic boundaries
- When you want section-level filtered retrieval

❌ **Avoid when:**
- Document is a PDF (Markdown headers won't be present in extracted text)
- Document has no header structure
- Headers are purely decorative (not semantic boundaries)

---

## PDF Workaround

PDFs don't have Markdown headers, but you can:
1. Convert the PDF to Markdown first (using tools like `marker-pdf` or `pymupdf4llm`)
2. Then ingest with Markdown chunking

```bash
# Install pymupdf4llm for PDF-to-Markdown conversion
uv add pymupdf4llm

# Convert
python -c "
import pymupdf4llm
md = pymupdf4llm.to_markdown('document.pdf')
open('document.md', 'w').write(md)
"
```
