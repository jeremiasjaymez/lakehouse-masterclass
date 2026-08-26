import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

import ollama
import requests

EMBEDDING_MODEL = "nomic-embed-text"
GENERATION_MODEL = "llama3.1"
MAX_CHUNK_CHARS = 1800


def load_markdown_documents(paths):
    docs = []
    for path in paths:
        source_path = path.as_posix()
        docs.append(
            {
                "source_path": source_path,
                "text": path.read_text(encoding="utf-8"),
            }
        )
    return docs


def find_corpus_files():
    docs_root = Path("docs/docs")
    lab_files = sorted((docs_root / "labs").glob("*.md"))
    return [docs_root / "guide.md", *lab_files]


def chunk_markdown_by_sections(document, max_chars=MAX_CHUNK_CHARS):
    sections = []
    current_title = "Introducción"
    current_lines = []

    for line in document["text"].splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading and current_lines:
            sections.extend(
                split_section(
                    document["source_path"],
                    current_title,
                    "\n".join(current_lines).strip(),
                    max_chars,
                )
            )
            current_lines = []

        if heading:
            current_title = heading.group(2).strip()

        current_lines.append(line)

    if current_lines:
        sections.extend(
            split_section(
                document["source_path"],
                current_title,
                "\n".join(current_lines).strip(),
                max_chars,
            )
        )

    return sections


def split_section(source_path, section_title, text, max_chars):
    if not text:
        return []

    parts = []
    current = []
    current_size = 0

    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if current and current_size + len(paragraph) > max_chars:
            parts.append("\n\n".join(current))
            current = []
            current_size = 0

        current.append(paragraph)
        current_size += len(paragraph)

    if current:
        parts.append("\n\n".join(current))

    return [
        {
            "source_path": source_path,
            "section_title": section_title,
            "chunk_index": index,
            "chunk_text": part,
        }
        for index, part in enumerate(parts)
    ]


def add_chunk_ids(chunks):
    for chunk in chunks:
        raw_id = "|".join(
            [
                chunk["source_path"],
                chunk["section_title"],
                str(chunk["chunk_index"]),
                chunk["chunk_text"],
            ]
        )
        chunk["chunk_id"] = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return chunks


def embed_text(text):
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]


def ask_ollama(prompt):
    payload = {
        "model": GENERATION_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    resp = requests.post(
        "http://localhost:11434/api/generate", json=payload, timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def build_rag_prompt(question, chunks):
    context = "\n\n".join(
        f"Fuente: {chunk['source_path']} :: {chunk['section_title']}\n{chunk['chunk_text']}"
        for chunk in chunks
    )
    return (
        "Sos un asistente de la Lakehouse Masterclass. "
        "Respondé solo con información del contexto recuperado. "
        "Si el contexto no alcanza, decí: 'No encontré evidencia suficiente en la documentación indexada'. "
        "No inventes pasos ni herramientas. Usá español rioplatense informal.\n\n"
        f"Contexto recuperado:\n{context}\n\n"
        f"Pregunta:\n{question}\n\n"
        "Respuesta:"
    )


def cosine_similarity(left, right):
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def build_knowledge_chunks():
    chunks = build_document_chunks()

    ingestion_ts = datetime.now(UTC)
    for chunk in chunks:
        chunk["embedding"] = embed_text(chunk["chunk_text"])
        chunk["ingestion_ts"] = ingestion_ts
    return chunks


def build_document_chunks():
    documents = load_markdown_documents(find_corpus_files())
    chunks = []
    for document in documents:
        chunks.extend(chunk_markdown_by_sections(document))

    return add_chunk_ids(chunks)


def rank_chunks(question_embedding, rows, top_k=3):
    ranked = []
    for row in rows:
        chunk = row.asDict(recursive=True)
        chunk["score"] = cosine_similarity(question_embedding, chunk["embedding"])
        ranked.append(chunk)
    return sorted(ranked, key=lambda chunk: chunk["score"], reverse=True)[:top_k]
