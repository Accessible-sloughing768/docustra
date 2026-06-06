"""
Chunking Strategies
═══════════════════
All strategies produce List[Document] compatible with Qdrant ingestion.

Strategies
──────────
Basic:
  recursive              RecursiveCharacterTextSplitter (default)
  character              CharacterTextSplitter
  token                  TokenTextSplitter (tiktoken)
  sentence_transformers  SentenceTransformersTokenTextSplitter

NLP-based:
  semantic               SemanticChunker — splits on topic-change detected via embeddings
  sentence_window        Index sentences; retrieve with ±N surrounding context

Structure-aware:
  markdown               MarkdownHeaderTextSplitter — preserves headers as metadata
  html                   HTMLHeaderTextSplitter — preserves HTML heading hierarchy

Advanced RAG patterns:
  parent_child           Small child chunks indexed; parent text stored in metadata
  hypothetical_questions LLM generates questions per chunk; questions used as embeddings
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from langchain_core.documents import Document

from docustra.core import get_logger, get_settings

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Enum
# ─────────────────────────────────────────────────────────────────────────────


class ChunkingStrategy(StrEnum):
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    SEMANTIC = "semantic"
    SENTENCE_WINDOW = "sentence_window"
    MARKDOWN = "markdown"
    HTML = "html"
    PARENT_CHILD = "parent_child"
    HYPOTHETICAL_QUESTIONS = "hypothetical_questions"


STRATEGY_DESCRIPTIONS: dict[ChunkingStrategy, str] = {
    ChunkingStrategy.RECURSIVE: "Default — splits on \\n\\n → \\n → . → space recursively",
    ChunkingStrategy.CHARACTER: "Splits on a single configurable character separator",
    ChunkingStrategy.TOKEN: "Splits by token count using tiktoken (cl100k_base)",
    ChunkingStrategy.SENTENCE_TRANSFORMERS: "Splits respecting the embedding model's token limit",
    ChunkingStrategy.SEMANTIC: "Splits where topic changes (detected via embedding similarity)",
    ChunkingStrategy.SENTENCE_WINDOW: "Indexes sentences; retrieves with ±N surrounding sentences",
    ChunkingStrategy.MARKDOWN: "Splits on # / ## / ### headers; preserves header hierarchy in metadata",
    ChunkingStrategy.HTML: "Splits on <h1>–<h4> tags; preserves header path in metadata",
    ChunkingStrategy.PARENT_CHILD: "Indexes small child chunks; parent text stored in metadata for retrieval",
    ChunkingStrategy.HYPOTHETICAL_QUESTIONS: "LLM generates questions per chunk; questions used as embedding text",
}


# ─────────────────────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────────────────────


class BaseChunker(ABC):
    strategy: ChunkingStrategy

    @abstractmethod
    def chunk(self, documents: list[Document]) -> list[Document]: ...

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[Document]:
        doc = Document(page_content=text, metadata=metadata or {})
        return self.chunk([doc])


# ─────────────────────────────────────────────────────────────────────────────
# 1. Recursive Character
# ─────────────────────────────────────────────────────────────────────────────


class RecursiveChunker(BaseChunker):
    """
    Tries to split on paragraph breaks first, then line breaks, sentences,
    words — producing chunks that respect natural text boundaries.
    Default and most versatile strategy.
    """

    strategy = ChunkingStrategy.RECURSIVE

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        return self._splitter.split_documents(documents)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Character
# ─────────────────────────────────────────────────────────────────────────────


class CharacterChunker(BaseChunker):
    """
    Splits on a single separator (default: double newline).
    Fast and predictable — useful when documents have consistent paragraph structure.
    """

    strategy = ChunkingStrategy.CHARACTER

    def __init__(
        self,
        separator: str = "\n\n",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        from langchain_text_splitters import CharacterTextSplitter

        settings = get_settings()
        self._splitter = CharacterTextSplitter(
            separator=separator,
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        return self._splitter.split_documents(documents)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Token
# ─────────────────────────────────────────────────────────────────────────────


class TokenChunker(BaseChunker):
    """
    Splits by token count using tiktoken (cl100k_base — same tokeniser as GPT-4).
    Ensures chunks never exceed the LLM's token window regardless of character count.
    chunk_size here means TOKEN count, not character count.
    """

    strategy = ChunkingStrategy.TOKEN

    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 32) -> None:
        from langchain_text_splitters import TokenTextSplitter

        self._splitter = TokenTextSplitter(
            encoding_name="cl100k_base",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        return self._splitter.split_documents(documents)


# ─────────────────────────────────────────────────────────────────────────────
# 4. SentenceTransformers Token
# ─────────────────────────────────────────────────────────────────────────────


class SentenceTransformersTokenChunker(BaseChunker):
    """
    Splits using the tokeniser of the embedding model itself.
    Guarantees no chunk exceeds the embedding model's max sequence length,
    preventing silent truncation during embedding.
    """

    strategy = ChunkingStrategy.SENTENCE_TRANSFORMERS

    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 32) -> None:
        from langchain_text_splitters import SentenceTransformersTokenTextSplitter

        settings = get_settings()
        self._splitter = SentenceTransformersTokenTextSplitter(
            model_name=settings.embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        return self._splitter.split_documents(documents)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Semantic
# ─────────────────────────────────────────────────────────────────────────────


class SemanticChunker(BaseChunker):
    """
    Embeds each sentence, then draws chunk boundaries where cosine similarity
    between adjacent sentences drops below a threshold (topic change).
    Produces context-coherent chunks at the cost of variable chunk size.
    Requires langchain-experimental.
    """

    strategy = ChunkingStrategy.SEMANTIC

    def __init__(self, breakpoint_threshold_type: str = "percentile") -> None:
        from langchain_experimental.text_splitter import SemanticChunker as _SemanticChunker

        from docustra.ingestion.embedder import get_embeddings

        self._splitter = _SemanticChunker(
            embeddings=get_embeddings(),
            breakpoint_threshold_type=breakpoint_threshold_type,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        results = []
        for doc in documents:
            try:
                chunks = self._splitter.create_documents(
                    [doc.page_content], metadatas=[doc.metadata]
                )
                for chunk in chunks:
                    chunk.metadata["chunking"] = "semantic"
                results.extend(chunks)
            except Exception as e:
                logger.warning("Semantic chunking failed for doc, falling back", error=str(e))
                results.append(doc)
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 6. Sentence Window
# ─────────────────────────────────────────────────────────────────────────────


class SentenceWindowChunker(BaseChunker):
    """
    Splits text into individual sentences using NLTK.
    Each sentence is indexed as a separate vector for precise retrieval.
    The surrounding window (±window_size sentences) is stored in metadata
    and returned to the LLM for richer context — giving precision + context.
    """

    strategy = ChunkingStrategy.SENTENCE_WINDOW

    def __init__(self, window_size: int = 3) -> None:
        self._window_size = window_size
        import nltk  # noqa: F401 — ensure available

    def chunk(self, documents: list[Document]) -> list[Document]:
        import nltk

        results = []
        for doc in documents:
            try:
                sentences = nltk.sent_tokenize(doc.page_content)
            except LookupError:
                # Fallback: split on ". " if punkt data not available
                sentences = [
                    s.strip() for s in re.split(r"(?<=[.!?])\s+", doc.page_content) if s.strip()
                ]

            for i, sentence in enumerate(sentences):
                start = max(0, i - self._window_size)
                end = min(len(sentences), i + self._window_size + 1)
                window_text = " ".join(sentences[start:end])

                results.append(
                    Document(
                        page_content=sentence,  # indexed vector
                        metadata={
                            **doc.metadata,
                            "window_context": window_text,  # returned to LLM
                            "sentence_index": i,
                            "window_size": self._window_size,
                            "chunking": "sentence_window",
                        },
                    )
                )
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 7. Markdown
# ─────────────────────────────────────────────────────────────────────────────


class MarkdownChunker(BaseChunker):
    """
    Splits on Markdown headers (# / ## / ###).
    Each chunk carries the full header path as metadata — e.g.
    {"h1": "Introduction", "h2": "Vector Indexes"}.
    Ideal for technical documentation, READMEs, and wiki pages.
    """

    strategy = ChunkingStrategy.MARKDOWN

    def __init__(
        self,
        headers: list[tuple[str, str]] | None = None,
        chunk_size: int | None = None,
    ) -> None:
        from langchain_text_splitters import (
            MarkdownHeaderTextSplitter,
            RecursiveCharacterTextSplitter,
        )

        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers
            or [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")],
            strip_headers=False,
        )
        settings = get_settings()
        self._size_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        results = []
        for doc in documents:
            md_chunks = self._header_splitter.split_text(doc.page_content)
            # Further split large sections while preserving header metadata
            for md_chunk in md_chunks:
                sub_chunks = self._size_splitter.split_documents([md_chunk])
                for sc in sub_chunks:
                    sc.metadata.update({**doc.metadata, **sc.metadata, "chunking": "markdown"})
                results.extend(sub_chunks)
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 8. HTML
# ─────────────────────────────────────────────────────────────────────────────


class HTMLChunker(BaseChunker):
    """
    Splits on HTML heading tags (<h1>–<h4>).
    Preserves the heading hierarchy in metadata as a breadcrumb path.
    Ideal for web-scraped content, HTML reports, and API documentation.
    """

    strategy = ChunkingStrategy.HTML

    def __init__(self, chunk_size: int | None = None) -> None:
        from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter

        self._header_splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=[
                ("h1", "h1"),
                ("h2", "h2"),
                ("h3", "h3"),
                ("h4", "h4"),
            ]
        )
        settings = get_settings()
        self._size_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        results = []
        for doc in documents:
            try:
                html_chunks = self._header_splitter.split_text(doc.page_content)
                for hc in html_chunks:
                    sub_chunks = self._size_splitter.split_documents([hc])
                    for sc in sub_chunks:
                        sc.metadata.update({**doc.metadata, **sc.metadata, "chunking": "html"})
                    results.extend(sub_chunks)
            except Exception as e:
                logger.warning("HTML chunking failed, falling back to recursive", error=str(e))
                fallback = RecursiveChunker()
                results.extend(fallback.chunk([doc]))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 9. Parent-Child
# ─────────────────────────────────────────────────────────────────────────────


class ParentChildChunker(BaseChunker):
    """
    Two-level chunking for retrieval precision + rich context:
      - Parent chunks (large, ~1024 chars) capture full context
      - Child chunks (small, ~256 chars) are indexed for precise vector search

    At query time, the child chunk is retrieved (high precision), but
    the parent text is returned to the LLM (rich context).
    The parent text is stored in child.metadata["parent_content"].
    """

    strategy = ChunkingStrategy.PARENT_CHILD

    def __init__(
        self,
        parent_chunk_size: int = 1024,
        child_chunk_size: int = 256,
        chunk_overlap: int = 32,
    ) -> None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self._parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )
        self._child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

    def chunk(self, documents: list[Document]) -> list[Document]:
        results = []
        for doc in documents:
            parents = self._parent_splitter.split_documents([doc])
            for p_idx, parent in enumerate(parents):
                children = self._child_splitter.split_documents([parent])
                for c_idx, child in enumerate(children):
                    child.metadata.update(
                        {
                            **parent.metadata,
                            "parent_content": parent.page_content,  # full context for LLM
                            "parent_index": p_idx,
                            "child_index": c_idx,
                            "chunking": "parent_child",
                        }
                    )
                    results.append(child)
        logger.info(
            "Parent-child chunking complete",
            parents=len(list({c.metadata["parent_index"] for c in results})),
            children=len(results),
        )
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 10. Hypothetical Questions
# ─────────────────────────────────────────────────────────────────────────────


class HypotheticalQuestionsChunker(BaseChunker):
    """
    For each chunk, uses the LLM to generate 3-5 questions the chunk answers.
    The QUESTIONS (not the chunk text) are used as the embedding text.

    Rationale: user queries look like questions; this aligns the embedding
    space between queries and indexed content — similar to HyDE but applied
    at ingestion time, not query time.

    ⚠️  Requires 1 LLM call per chunk. Use with small documents or paid tiers.
    """

    strategy = ChunkingStrategy.HYPOTHETICAL_QUESTIONS

    def __init__(self, questions_per_chunk: int = 3) -> None:
        self._questions_per_chunk = questions_per_chunk

    def chunk(self, documents: list[Document]) -> list[Document]:
        from langchain_core.prompts import ChatPromptTemplate

        from docustra.retrieval.base import get_llm

        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"Generate exactly {self._questions_per_chunk} distinct questions "
                    "that this text passage answers. Return one question per line, no numbering.",
                ),
                ("human", "{text}"),
            ]
        )
        results = []
        for doc in documents:
            try:
                chain = prompt | llm
                raw = chain.invoke({"text": doc.page_content[:1000]}).content.strip()
                questions = [q.strip() for q in raw.splitlines() if q.strip()][
                    : self._questions_per_chunk
                ]

                for q_idx, question in enumerate(questions):
                    results.append(
                        Document(
                            page_content=question,  # embedded — looks like a user query
                            metadata={
                                **doc.metadata,
                                "original_content": doc.page_content,  # returned to LLM
                                "question_index": q_idx,
                                "chunking": "hypothetical_questions",
                            },
                        )
                    )
            except Exception as e:
                logger.warning(
                    "HypQ generation failed, falling back to original chunk", error=str(e)
                )
                results.append(doc)
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY: dict[ChunkingStrategy, type[BaseChunker]] = {
    ChunkingStrategy.RECURSIVE: RecursiveChunker,
    ChunkingStrategy.CHARACTER: CharacterChunker,
    ChunkingStrategy.TOKEN: TokenChunker,
    ChunkingStrategy.SENTENCE_TRANSFORMERS: SentenceTransformersTokenChunker,
    ChunkingStrategy.SEMANTIC: SemanticChunker,
    ChunkingStrategy.SENTENCE_WINDOW: SentenceWindowChunker,
    ChunkingStrategy.MARKDOWN: MarkdownChunker,
    ChunkingStrategy.HTML: HTMLChunker,
    ChunkingStrategy.PARENT_CHILD: ParentChildChunker,
    ChunkingStrategy.HYPOTHETICAL_QUESTIONS: HypotheticalQuestionsChunker,
}


def get_chunker(
    strategy: ChunkingStrategy | str = ChunkingStrategy.RECURSIVE, **kwargs: Any
) -> BaseChunker:
    if isinstance(strategy, str):
        strategy = ChunkingStrategy(strategy)
    cls = _REGISTRY.get(strategy)
    if cls is None:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    return cls(**kwargs)


# Backward-compatible alias
DocumentChunker = RecursiveChunker
