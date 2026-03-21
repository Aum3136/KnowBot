import streamlit as st
import os
from test.rag_chain import load_rag_chain, get_answer
from transcribe import transcribe_meeting, summarize_transcript

# Page config — this controls browser tab title and layout
st.set_page_config(
    page_title="KnowBot — IT Knowledge Assistant",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-title { font-size: 28px; font-weight: 600; color: #1a1a2e; }
    .subtitle   { font-size: 14px; color: #666; margin-bottom: 20px; }
    .source-box { background: #f0f4ff; border-left: 3px solid #4169e1;
                  padding: 10px; border-radius: 4px; font-size: 13px; }
    .stChatMessage { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### KnowBot")
    st.markdown("*AI-powered company knowledge assistant*")
    st.divider()

    # Document uploader in sidebar
    st.markdown("**Upload Documents**")
    uploaded_files = st.file_uploader(
        "Add PDF, PPTX, or XLSX files",
        type=["pdf", "pptx", "xlsx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        os.makedirs("data", exist_ok=True)
        for f in uploaded_files:
            with open(os.path.join("data", f.name), "wb") as out:
                out.write(f.getbuffer())
        if st.button("Index Documents", type="primary"):
            with st.spinner("Indexing documents..."):
                os.system("python ingest.py")
            st.success("Documents indexed successfully!")
            st.cache_resource.clear()

    st.divider()
    st.markdown("**About**")
    st.markdown("KnowBot helps IT employees instantly find answers from company documents — HR policies, onboarding guides, project trackers, and more.")
    st.markdown("*SDG 8 — Decent Work & Economic Growth*")

# Load RAG chain (cached so it doesn't reload every message)
@st.cache_resource
def get_chain():
    try:
        return load_rag_chain()
    except FileNotFoundError:
        return None

# Navigation tabs
tab1, tab2 = st.tabs(["Document Q&A", "Meeting Summarizer"])

# ---- TAB 1: Document Q&A ----
with tab1:
    st.markdown('<p class="main-title">Ask Your Company Documents</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Get instant answers from HR policies, onboarding guides, project trackers, and more.</p>', unsafe_allow_html=True)

    chain = get_chain()

    if chain is None:
        st.warning("No documents indexed yet. Upload documents using the sidebar and click 'Index Documents'.")
    else:
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Suggested questions (helps during demo)
        if not st.session_state.messages:
            st.markdown("**Try asking:**")
            cols = st.columns(3)
            suggestions = [
                "What is the leave policy?",
                "How do I onboard a new developer?",
                "What is the escalation process?"
            ]
            for i, suggestion in enumerate(suggestions):
                if cols[i].button(suggestion, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "sources" in msg:
                    with st.expander("Sources"):
                        st.markdown(f'<div class="source-box">{msg["sources"]}</div>', unsafe_allow_html=True)

        # Chat input
        if question := st.chat_input("Ask anything about company policies, processes, or projects..."):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching documents..."):
                    answer, source_names, raw_sources = get_answer(chain, question)

                st.write(answer)

                if source_names:
                    sources_text = "**Found in:** " + " | ".join(source_names)
                    with st.expander("View Sources"):
                        st.markdown(f'<div class="source-box">{sources_text}</div>', unsafe_allow_html=True)
                        for doc in raw_sources[:2]:
                            st.caption(f"...{doc.page_content[:200]}...")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": " | ".join(source_names) if source_names else ""
                })

        # Clear chat button
        if st.session_state.messages:
            if st.button("Clear Chat"):
                st.session_state.messages = []
                st.rerun()

# ---- TAB 2: Meeting Summarizer ----
with tab2:
    st.markdown('<p class="main-title">Meeting Transcription & Summary</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload a meeting recording and get an instant summary with action items.</p>', unsafe_allow_html=True)

    audio_file = st.file_uploader("Upload meeting audio (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

    if audio_file:
        os.makedirs("temp", exist_ok=True)
        audio_path = os.path.join("temp", audio_file.name)
        with open(audio_path, "wb") as f:
            f.write(audio_file.getbuffer())

        if st.button("Transcribe & Summarize", type="primary"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Transcript**")
                with st.spinner("Transcribing audio..."):
                    transcript = transcribe_meeting(audio_path)
                st.text_area("", transcript, height=300)

            with col2:
                st.markdown("**AI Summary & Action Items**")
                with st.spinner("Generating summary..."):
                    summary = summarize_transcript(transcript)
                st.markdown(summary)
