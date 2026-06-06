# Sentence Transformers Token Splitter

**Strategy ID:** `sentence_transformers` | **LLM Required:** No

## What It Does

Splits text using the **tokeniser of the actual embedding model** (`sentence-transformers/all-MiniLM-L6-v2`). This is the most precise way to ensure chunks never silently exceed the embedding model's maximum sequence length (256 tokens for all-MiniLM-L6-v2).

---

## The Silent Truncation Problem

Most embedding models have a hard maximum token limit. If your chunk exceeds it, the model **silently truncates** — embedding only the first N tokens and ignoring the rest. This means:

```
Chunk (700 chars ≈ 180 tokens):
"Vector databases store high-dimensional vectors... [first 256 tokens]
 ...alongside payload metadata for filtering [TRUNCATED — never embedded]"

The second half of the chunk is invisible to retrieval.
```

`SentenceTransformersTokenChunker` prevents this entirely by splitting at the model's exact token boundary.

---

## How It Works

```
Embedding model: all-MiniLM-L6-v2
Max sequence length: 256 tokens
chunk_size: 256 tokens, chunk_overlap: 32 tokens

Input text is tokenised using the SAME tokeniser as the embedding model.
Text is split at exactly 256-token boundaries with 32-token overlap.

→ Every chunk is guaranteed to fit within one forward pass of the model.
→ No truncation. No lost content.
```

---

## Comparison: Token vs SentenceTransformers

| | TokenTextSplitter | SentenceTransformersTokenSplitter |
|---|---|---|
| Tokeniser | tiktoken (cl100k_base) | sentence-transformers model tokeniser |
| Purpose | LLM input compliance | Embedding model compliance |
| Risk addressed | LLM context overflow | Embedding silent truncation |
| Token count | GPT-4 tokens | Model-specific tokens (may differ) |

Use both together if you need both — chunk with SentenceTransformers, then verify against LLM limits.

---

## Configuration

```json
{
  "chunking_strategy": "sentence_transformers",
  "chunking_params": {
    "chunk_size": 256,
    "chunk_overlap": 32
  }
}
```

The `model_name` is automatically read from `EMBEDDING_MODEL` in `.env`:
```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Metadata Produced

```python
{"source": "document.pdf", "page": 1, "type": "text"}
```

---

## When to Use

✅ **Best for:**
- Any document where you want to guarantee complete embedding coverage
- When you've observed retrieval gaps in dense documents (sign of truncation)
- Switching embedding models — this auto-adjusts to the new model's limits
- Production systems where silent truncation is unacceptable

❌ **Avoid when:**
- Your chunks are already short (under 100 tokens) — no truncation risk
- You're prioritising semantic coherence over technical precision (use `semantic`)

---

## Verifying Truncation in Your Current Collection

```python
from docustra.ingestion.embedder import get_embeddings
emb = get_embeddings()
max_len = emb.client.max_seq_length  # e.g. 256 for all-MiniLM-L6-v2
print(f"Max tokens: {max_len}")
```

If you have chunks longer than this, switch to `sentence_transformers` strategy.
