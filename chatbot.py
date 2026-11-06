"""
chatbot.py - keeps the conversation (history) and talks to the RAG pipeline.
Streamlit pages store one Chatbot object in st.session_state.
"""
from datetime import datetime
from typing import Dict, List

from modules.rag_pipeline import RAGPipeline

SUGGESTED_QUESTIONS = [
    "What is groundwater?",
    "What is groundwater depletion and what causes it?",
    "How can groundwater be recharged?",
    "Explain the groundwater resource assessment report.",
    "What does the report say about Punjab?",
    "What is the stage of groundwater extraction?",
]


class Chatbot:
    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline
        self.history: List[Dict] = []     # [{'role','content','citations','time'}]

    def ask(self, question: str) -> Dict:
        """Answer a question, remember both turns, return the answer record."""
        result = self.pipeline.answer(question, self.history)
        now = datetime.now().strftime("%H:%M")
        self.history.append({"role": "user", "content": question.strip(), "time": now})
        self.history.append({"role": "assistant", "content": result["answer"],
                             "citations": result["citations"], "mode": result["mode"],
                             "time": now})
        return result

    def clear(self) -> None:
        self.history = []

    def export_text(self) -> str:
        """Conversation as plain text for the Download button."""
        lines = ["AI Groundwater Information Assistant - conversation export", ""]
        for turn in self.history:
            who = "You" if turn["role"] == "user" else "Assistant"
            lines.append(f"[{turn['time']}] {who}: {turn['content']}")
            for c in turn.get("citations", []):
                lines.append(f"    source: {c['document']}, p. {c['page']}")
            lines.append("")
        return "\n".join(lines)
