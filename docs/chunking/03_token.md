# Token Text Splitter

**Strategy ID:** `token` | **LLM Required:** No

## What It Does

Splits text by **token count** using OpenAI's `tiktoken` library (cl100k_base encoding — the same tokeniser used by GPT-4 and Claude). The `chunk_size` parameter means **tokens**, not characters.

This is critical when your RAG pipeline feeds chunks into an LLM with a strict context window — a 512-character chunk might be 100 tokens or 200 tokens depending on the language and punctuation.

---

## Why Tokens vs Characters Matter

```
"Hello world"           → 2 tokens  (5 chars/token avg)
"supercalifragilistic"  → 6 tokens  (3 chars/token avg)
"日本語テキスト"          → 14 tokens (1 char/token avg — CJK is expensive)
"{'key': 'value'}"     → 7 tokens  (special chars are multi-token)
```

If you're chunking a multilingual document with English + Japanese text using `chunk_size=512 chars`, some chunks might have 400 tokens and others 150 — very uneven. Token-based splitting gives consistent LLM context usage.

---

## How It Works

```
Input:
"Apple reported revenue of $383 billion in FY2023,
 driven by strong iPhone sales of $200 billion.
 Services grew 9% to $85 billion..."

chunk_size=50 tokens, chunk_overlap=10 tokens

Tokenise entire text:
[Apple][reported][revenue][of][$][383][billion][in][FY][2023],
[driven][by][strong][i][Phone][sales][of][$][200][billion].
[Services][grew][9][%][to][$][85][billion]...

Split at 50-token boundary:
Chunk 1 (tokens 1-50):  "Apple reported revenue of $383 billion..."
Chunk 2 (tokens 41-90): "...in FY2023, driven by strong iPhone..."  ← 10-token overlap
Chunk 3 (tokens 81-..): "...Services grew 9% to $85 billion..."
```

---

## Configuration

```env
# Note: for Token strategy, CHUNK_SIZE is in TOKENS not characters
# Default token chunk = 256 tokens ≈ ~1024 characters
```

Via API:
```json
{
  "chunking_strategy": "token",
  "chunking_params": {
    "chunk_size": 256,
    "chunk_overlap": 32
  }
}
```

**Token count guidelines:**
| Model | Max context | Recommended chunk_size |
|---|---|---|
| Gemini 2.5 Flash | 1M tokens | 512–1024 |
| GPT-4o | 128K tokens | 256–512 |
| Llama 3.3 70B | 128K tokens | 256–512 |
| Groq (free tier) | 8K tokens | 128–256 |

---

## Metadata Produced

```python
{"source": "document.pdf", "page": 2, "type": "text"}
```

---

## Demo Example

**Document:** Apple 10-K filing with dense financial tables

```
Input section (financial data — dense, many numbers):
"Total net revenues were $383,285 million, $394,328 million and $365,817 million
for 2023, 2022 and 2021, respectively. iPhone net revenues decreased 2.8%..."

Character count: 248 chars
Token count: 71 tokens  ← very different!

With chunk_size=512 chars: might combine this with next paragraph
With chunk_size=50 tokens: this section fits exactly as one chunk
```

Using token chunking ensures this dense table row is its own atomic chunk regardless of character length.

---

## When to Use

✅ **Best for:**
- Multilingual documents (CJK languages, Arabic, etc.)
- Documents with dense code or structured data (JSON, tables, formulas)
- When you're passing chunks directly to an LLM with a known token limit
- Ensuring even distribution of context across chunks

❌ **Avoid when:**
- Document is pure English prose (character chunking works fine)
- You don't need strict token counting
- Processing speed is more important than token precision

---

## Dependencies

`tiktoken` — already installed as part of `langchain` dependencies. No additional setup required.
