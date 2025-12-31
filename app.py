import streamlit as st
from researcher import search_arxiv, generate_review

st.set_page_config(page_title="AI Researcher MVP", layout="wide")

st.title("🎓 AI Researcher Assistant")
st.markdown("I help you find papers and write literature reviews.")

# Sidebar for configuration
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for generating the review.")
    st.info("Your API key is not saved and only used for this session.")

# Main Area
topic = st.text_input("Enter your research topic/keywords:", placeholder="e.g., 'Agentic Workflow in Large Language Models'")

if 'papers' not in st.session_state:
    st.session_state.papers = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📚 Search Results")
    if st.button("Search ArXiv", type="primary"):
        with st.spinner("Searching ArXiv..."):
            st.session_state.papers = search_arxiv(topic, max_results=10)
        
    if st.session_state.papers:
        st.success(f"Found {len(st.session_state.papers)} papers.")
        for p in st.session_state.papers:
            with st.expander(f"📄 {p.title} ({p.published})"):
                st.markdown(f"**Authors:** {', '.join(p.authors)}")
                st.markdown(f"**Abstract:** {p.summary}")
                st.markdown(f"[PDF Link]({p.url})")
    else:
        st.info("Enter a topic and click Search to find papers.")

with col2:
    st.subheader("📝 Literature Review")
    if st.button("Generate Review"):
        if not st.session_state.papers:
            st.warning("Please search for papers first.")
        elif not api_key:
            st.error("Please enter your OpenAI API Key in the sidebar.")
        else:
            with st.spinner("Reading papers and writing review... (this may take a minute)"):
                review = generate_review(st.session_state.papers, api_key, topic)
                st.markdown(review)
