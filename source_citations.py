"""
source_citations.py - builds readable citations from retrieved chunks.

A citation always comes from a chunk that was really retrieved, so it can only
name a report and page that exist in the vector store - nothing is invented.
"""
from typing import Dict, List


def make_citations(hits: List[Dict]) -> List[Dict]:
    """Merge hits into unique (document, page) citations, best score first."""
    seen: Dict[tuple, Dict] = {}
    for hit in hits:
        key = (hit["document"], hit["page"])
        if key not in seen or hit["score"] > seen[key]["score"]:
            seen[key] = {"document": hit["document"], "page": hit["page"], "score": hit["score"],
                         "excerpt": hit["text"][:300].strip()}
    return sorted(seen.values(), key=lambda c: -c["score"])


def format_citation(c: Dict) -> str:
    return f"{c['document']}, p. {c['page']}"


def citations_markdown(citations: List[Dict]) -> str:
    if not citations:
        return ""
    return "**Sources**\n" + "\n".join(f"- {format_citation(c)}" for c in citations)


def build_context(hits: List[Dict]) -> str:
    """Numbered context block that is sent to the LLM: [1] (report, p. X): text"""
    return "\n\n".join(f"[{i}] ({h['document']}, p. {h['page']}): {h['text']}"
                       for i, h in enumerate(hits, 1))
