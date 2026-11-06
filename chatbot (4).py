"""AI Groundwater Assistant - the central feature: chat grounded in indexed reports."""
import streamlit as st

import ui
from modules.chatbot import SUGGESTED_QUESTIONS
from modules.source_citations import format_citation

ui.setup_page("AI Groundwater Assistant", "Answers come only from the reports you have indexed.")
bot = ui.get_chatbot()

top = st.columns([1, 1, 4])
if top[0].button("🗑️ Clear conversation"):
    bot.clear()
    st.rerun()
if bot.history:
    top[1].download_button("⬇️ Download", bot.export_text(), file_name="groundwater_chat.txt")

if bot.pipeline.store.count() == 0:
    st.warning("No reports are indexed yet, so the assistant cannot answer. "
               "Add a government PDF in **Document Library** first.")

# Suggested questions (only while the chat is empty)
clicked = None
if not bot.history:
    st.caption("Try a suggested question:")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if cols[i % 2].button(q, key=f"sq{i}", width="stretch"):
            clicked = q

for turn in bot.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        for c in turn.get("citations", []):
            st.markdown(f"<div class='src'>📄 {format_citation(c)} · relevance {c['score']:.2f}</div>",
                        unsafe_allow_html=True)

question = st.chat_input("Ask about groundwater...") or clicked
if question:
    if len(question) > 1000:
        st.error("Please keep questions under 1000 characters.")
    else:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching the reports..."):
                try:
                    bot.ask(question)
                except Exception as exc:
                    st.error(f"Something went wrong: {exc}")
        st.rerun()
