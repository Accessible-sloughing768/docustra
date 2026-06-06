# Recursive Character Text Splitter

**Strategy ID:** `recursive` | **Default:** Yes | **LLM Required:** No

## What It Does

The `RecursiveCharacterTextSplitter` attempts to split text at the most natural boundary first, then falls back to smaller boundaries only when necessary. It works through a hierarchy of separators:

```
1. "\n\n"  — paragraph break (try this first)
2. "\n"    — line break
3. ". "    — sentence boundary
4. " "     — word boundary
5. ""      — character (last resort)
```

This produces chunks that respect natural text structure — paragraphs stay together when they fit, sentences are only split when a paragraph is too large, and words are only split as a last resort.

---

## How It Works

```
Input text (2000 chars):
┌─────────────────────────────────────────────────────┐
│ Paragraph 1 (300 chars)\n\n                         │
│ Paragraph 2 (400 chars)\n\n                         │
│ Paragraph 3 (600 chars)\n\n                         │
│ Paragraph 4 (700 chars)                             │
└─────────────────────────────────────────────────────┘

chunk_size = 512, chunk_overlap = 64

Step 1: Try splitting on "\n\n"
  → [P1 (300), P2 (400), P3 (600), P4 (700)]

Step 2: P1+P2 = 700 chars — fits in 512? No. Keep separate.
  → [P1, P2, P3, P4]

Step 3: P3 = 600 > 512 — recurse on P3 using "\n"
  → [P3a (280), P3b (320)]

Step 4: Apply overlap (64 chars from prev chunk added to start)
  → Final: [P1, P2, P3a_with_overlap, P3b_with_overlap, P4]
```

---

## Configuration

```env
# .env
CHUNK_SIZE=512    # maximum characters per chunk
CHUNK_OVERLAP=64  # overlap characters between chunks
```

**Custom separators** (via API `chunking_params`):
```json
{
  "chunking_strategy": "recursive",
  "chunking_params": {
    "chunk_size": 1024,
    "chunk_overlap": 128
  }
}
```

---

## Metadata Produced

```python
{
  "source": "vector-databases-guide.pdf",
  "page": 3,
  "type": "text"
}
```

No additional metadata beyond source/page — standard output.

---

## Demo Example

**Input text (from vector-databases-guide.pdf, page 19):**
```
Vector databases are specialized in storing, compressing, indexing, and retrieving 
vectors more efficiently than databases that are designed for relational, unstructured, 
graph, or structured data. They are built from the ground up with vector operations 
in mind.

Unlike traditional databases that store rows and columns, vector databases store 
high-dimensional vectors alongside metadata. Each vector represents an embedding 
of a piece of data...
```

**After recursive chunking (chunk_size=512):**
```
Chunk 1 (412 chars):
  "Vector databases are specialized in storing, compressing..."
  [full first paragraph — fits within 512]

Chunk 2 (368 chars + 64 overlap):
  "...alongside metadata. Each vector represents an embedding" [overlap]
  "Unlike traditional databases that store rows and columns..."
  [second paragraph with overlap from chunk 1 tail]
```

---

## When to Use

✅ **Best for:**
- General-purpose document ingestion
- Mixed content (paragraphs, lists, tables as text)
- When you're unsure which strategy to pick
- First-pass ingestion before fine-tuning

❌ **Avoid when:**
- Document is Markdown with clear headers (use `markdown`)
- You need LLM-aligned token counts (use `token`)
- Retrieval precision is critical (use `parent_child`)

---

## Performance

| Metric | Value |
|---|---|
| Throughput | ~10,000 chars/ms (CPU) |
| Chunk consistency | Variable ±20% around chunk_size |
| Split quality | Good — respects paragraph/sentence boundaries |
| Extra dependencies | None |
