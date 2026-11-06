"""
document_processor.py - turns a PDF into clean, page-tagged chunks.

Steps (the first half of the RAG pipeline):
  1. Open the PDF with PyMuPDF and extract text page by page.
  2. Keep the document name and page number with every piece of text.
  3. Clean the text (fix hyphenated line breaks, collapse whitespace).
  4. Split each page into overlapping chunks with LangChain's splitter.
"""
import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import pymupdf  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


class PDFProcessingError(Exception):
    """Raised when a PDF cannot be read or contains no extractable text."""


@dataclass
class Chunk:
    """One searchable piece of a document."""
    text: str
    document: str          # file name of the PDF
    page: int              # 1-based page number in the PDF
    chunk_id: str          # unique id (document hash + page + index)
    metadata: Dict = field(default_factory=dict)


def file_hash(path: Path) -> str:
    """Short SHA-256 fingerprint; used to detect duplicate uploads."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def clean_text(text: str) -> str:
    """Basic clean-up of text extracted from a PDF."""
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(?=[a-z])", "", text)      # join words split by a hyphen at line end
    text = re.sub(r"[ \t]+", " ", text)           # collapse spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse many blank lines
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # single newline -> space (re-flow paragraphs)
    return text.strip()


def extract_pages(pdf_path: Path) -> List[Dict]:
    """Return [{'page': 1, 'text': '...'}, ...] for pages that contain text.

    Raises PDFProcessingError for missing/corrupt/empty (e.g. scanned) PDFs.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise PDFProcessingError(f"File not found: {pdf_path.name}")
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        raise PDFProcessingError(f"Cannot open '{pdf_path.name}' as a PDF: {exc}") from exc

    pages = []
    try:
        for index in range(doc.page_count):
            text = clean_text(doc[index].get_text("text"))
            if text:
                pages.append({"page": index + 1, "text": text})
        total = doc.page_count
    finally:
        doc.close()

    if not pages:
        raise PDFProcessingError(
            f"'{pdf_path.name}' ({total} pages) has no extractable text. "
            "It may be a scanned image PDF; OCR would be needed.")
    return pages


def split_pages(pages: List[Dict], document: str, doc_hash: str,
                chunk_size: int = config.CHUNK_SIZE,
                chunk_overlap: int = config.CHUNK_OVERLAP) -> List[Chunk]:
    """Split page texts into chunks; every chunk remembers its page number."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        separators=["\n\n", ". ", " ", ""])
    chunks: List[Chunk] = []
    for page in pages:
        for i, piece in enumerate(splitter.split_text(page["text"])):
            piece = piece.strip()
            if len(piece) < 20:        # skip tiny fragments (page numbers etc.)
                continue
            chunks.append(Chunk(
                text=piece, document=document, page=page["page"],
                chunk_id=f"{doc_hash}-p{page['page']}-c{i}",
                metadata={"document": document, "page": page["page"], "doc_hash": doc_hash}))
    return chunks


def process_pdf(pdf_path: Path) -> Dict:
    """Full pipeline for one PDF. Returns a dict with chunks and page statistics."""
    pdf_path = Path(pdf_path)
    pages = extract_pages(pdf_path)
    doc_hash = file_hash(pdf_path)
    chunks = split_pages(pages, pdf_path.name, doc_hash)
    with pymupdf.open(pdf_path) as doc:
        total_pages = doc.page_count
    return {"document": pdf_path.name, "doc_hash": doc_hash, "total_pages": total_pages,
            "pages_with_text": len(pages), "chunks": chunks}
