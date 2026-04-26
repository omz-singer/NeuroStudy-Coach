"""
src/ui/chatbot.py
AI Study Assistant page powered by Anthropic Claude.
Supports text chat and document upload for context.
"""

import os
import base64
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are NeuroStudy Coach, a friendly and supportive AI study assistant 
specifically designed to help neurodivergent students (ADHD, Autism, Dyslexia, Dyscalculia) 
with their academic work.

Your approach:
- Be patient, clear, and encouraging
- Break complex concepts into small, digestible steps
- Use examples, analogies, and visual descriptions when helpful
- Avoid overwhelming the student with too much information at once
- Celebrate progress and effort, not just results
- If a student seems frustrated, acknowledge it and offer a different approach
- For reading/writing tasks, offer to simplify or restructure information
- For math/problem sets, walk through step by step
- Always check for understanding before moving on

You can help with:
- Explaining difficult concepts
- Summarizing documents or notes
- Creating study guides or flashcard-style Q&A
- Quizzing the student on material
- Breaking down assignment requirements
- Suggesting study strategies tailored to neurodivergent learners
- Providing encouragement and motivation

Keep responses concise and well-structured. Use bullet points and numbered lists 
when explaining multi-step processes. Always be warm and supportive."""


def _get_client():
    """Get Anthropic client."""
    try:
        import anthropic
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        return None


def _send_message(messages: list, uploaded_content: str = None) -> str:
    """Send messages to Claude and get response."""
    client = _get_client()
    if client is None:
        return "Error: Could not connect to AI service. Please check your API key."

    try:
        # Build messages for API
        api_messages = []

        for msg in messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # If there's uploaded content, inject it into the last user message
        if uploaded_content and api_messages:
            last = api_messages[-1]
            if last["role"] == "user":
                last["content"] = f"I've uploaded a document for reference:\n\n{uploaded_content}\n\n---\n\n{last['content']}"

        import anthropic
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=api_messages,
        )
        return response.content[0].text

    except Exception as e:
        return f"Error getting response: {str(e)}"


def _extract_file_text(uploaded_file) -> str:
    """Extract text from uploaded file."""
    name = uploaded_file.name.lower()

    try:
        if name.endswith(".txt") or name.endswith(".md"):
            return uploaded_file.read().decode("utf-8")

        elif name.endswith(".pdf"):
            try:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages)
            except Exception:
                try:
                    import PyPDF2
                    import io
                    reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    return "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    return ""

        elif name.endswith(".docx"):
            try:
                import docx
                import io
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                return ""

    except Exception:
        return ""

    return ""


def render_chatbot_page() -> None:
    st.header("🤖 Study Assistant")
    st.caption("Your personal AI tutor — ask anything, upload your notes, and get help tailored for you.")

    # Check API key
    if not ANTHROPIC_API_KEY:
        st.error("⚠️ No API key found. Make sure your `.env` file contains `ANTHROPIC_API_KEY=your-key`.")
        return

    # ── Document Upload ────────────────────────────────────────────────────────
    with st.expander("📎 Upload Study Material (optional)", expanded=False):
        st.caption("Upload notes, a PDF, or a document and the assistant will use it to answer your questions.")
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["pdf", "txt", "md", "docx"],
            key="chatbot_upload"
        )

        if uploaded_file:
            if "uploaded_text" not in st.session_state or st.session_state.get("uploaded_filename") != uploaded_file.name:
                with st.spinner("Reading document..."):
                    text = _extract_file_text(uploaded_file)
                    if text:
                        # Truncate to avoid token limits
                        st.session_state.uploaded_text = text[:8000]
                        st.session_state.uploaded_filename = uploaded_file.name
                        st.success(f"✅ **{uploaded_file.name}** loaded — ask me anything about it!")
                    else:
                        st.warning("Could not extract text from this file.")
                        st.session_state.uploaded_text = None
                        st.session_state.uploaded_filename = None
        else:
            # Clear uploaded content if file removed
            if "uploaded_text" in st.session_state:
                del st.session_state.uploaded_text
            if "uploaded_filename" in st.session_state:
                del st.session_state.uploaded_filename

    # Show active document badge
    if st.session_state.get("uploaded_filename"):
        st.markdown(
            f'<div style="background:#1e3a5f;border-radius:8px;padding:6px 12px;'
            f'margin-bottom:8px;font-size:0.8rem;color:#93c5fd;display:inline-block;">'
            f'📄 Using: <strong>{st.session_state.uploaded_filename}</strong></div>',
            unsafe_allow_html=True,
        )

    # ── Chat History ───────────────────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Render chat messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Welcome message if no history
    if not st.session_state.chat_messages:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 Hi! I'm your NeuroStudy Coach assistant. I'm here to help you understand "
                "your coursework, break down tricky concepts, quiz you on material, or just "
                "talk through what you're working on.\n\n"
                "You can also upload your notes or a document above and I'll use it to answer "
                "your questions. What would you like help with today?"
            )

    # ── Chat Input ─────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                uploaded_content = st.session_state.get("uploaded_text", None)
                response = _send_message(
                    st.session_state.chat_messages,
                    uploaded_content=uploaded_content,
                )
            st.markdown(response)

        # Save assistant response
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

    # ── Clear Chat Button ──────────────────────────────────────────────────────
    if st.session_state.chat_messages:
        if st.button("🗑️ Clear Chat", use_container_width=False):
            st.session_state.chat_messages = []
            st.rerun()
