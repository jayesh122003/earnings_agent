import os
import sys
import re
import time

import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENT_DIR = os.path.join(ROOT_DIR, "agent")

if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from agent import run_agent, COMPANY_TO_TICKER


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Earnings Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Bloomberg-terminal-inspired theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ─────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0E1117;
    color: #C9D1D9;
}

[data-testid="stSidebar"] {
    background-color: #0B0E14;
    border-right: 1px solid #1E2530;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem;
}

/* ── Header bar ─────────────────────────────────────────────────────── */
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 0;
    border-bottom: 2px solid #FF6A00;
    margin-bottom: 1.5rem;
}

.header-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    color: #FF6A00;
    letter-spacing: 0.5px;
}

.header-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #6E7681;
    margin-top: 2px;
}

.header-status {
    display: flex;
    gap: 1.2rem;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #6E7681;
}

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}

.status-dot.green { background-color: #3FB950; }
.status-dot.amber { background-color: #FF6A00; }
.status-dot.red   { background-color: #F85149; }

/* ── Sidebar sections ───────────────────────────────────────────────── */
.sidebar-section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    color: #6E7681;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.6rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid #1E2530;
}

.context-card {
    background: #161B22;
    border: 1px solid #1E2530;
    border-radius: 6px;
    padding: 0.9rem;
    margin-bottom: 0.8rem;
}

.context-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #6E7681;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.context-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem;
    font-weight: 600;
    color: #E6EDF3;
    margin-top: 2px;
}

.context-value.active {
    color: #FF6A00;
}

/* ── Company pills ──────────────────────────────────────────────────── */
.company-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.company-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    background: #161B22;
    border: 1px solid #1E2530;
    color: #8B949E;
    padding: 3px 10px;
    border-radius: 4px;
    letter-spacing: 0.5px;
}

.company-pill.active {
    border-color: #FF6A00;
    color: #FF6A00;
    background: rgba(255, 106, 0, 0.08);
}

/* ── Chat messages ──────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #161B22;
    border: 1px solid #1E2530;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    background: #0D1117;
    border-left: 3px solid #FF6A00;
}

/* Force consistent text rendering inside chat — prevents Streamlit theme
   from applying primaryColor to bold/links in LLM output */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span:not(.citation-badge) {
    color: #C9D1D9 !important;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    line-height: 1.65;
}

[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] b {
    color: #E6EDF3 !important;
    font-weight: 600;
}

[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] i {
    color: #C9D1D9 !important;
}

[data-testid="stChatMessage"] a {
    color: #FF6A00 !important;
    text-decoration: none;
}

[data-testid="stChatMessage"] code {
    background: #1E2530;
    color: #C9D1D9;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}

[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] ol {
    padding-left: 1.2rem;
}

[data-testid="stChatMessage"] ul li::marker {
    color: #FF6A00;
}

/* ── Citation cards ─────────────────────────────────────────────────── */
.citation-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 0.8rem;
    padding-top: 0.7rem;
    border-top: 1px solid #1E2530;
}

.citation-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    background: rgba(255, 106, 0, 0.1);
    border: 1px solid rgba(255, 106, 0, 0.25);
    color: #FF6A00;
    padding: 3px 8px;
    border-radius: 3px;
    letter-spacing: 0.3px;
}

/* ── Reasoning panel ────────────────────────────────────────────────── */
.reasoning-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1E2530;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
}

.reasoning-step:last-child {
    border-bottom: none;
}

.step-icon {
    font-size: 0.85rem;
    min-width: 22px;
    text-align: center;
    margin-top: 1px;
}

.step-label {
    color: #8B949E;
}

.step-detail {
    color: #C9D1D9;
    font-weight: 500;
}

.step-time {
    color: #6E7681;
    font-size: 0.65rem;
    margin-left: auto;
    white-space: nowrap;
}

/* ── Input area ─────────────────────────────────────────────────────── */
[data-testid="stChatInput"] > div {
    border-color: #1E2530 !important;
    background-color: #161B22 !important;
}

[data-testid="stChatInput"] input {
    color: #C9D1D9 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.stButton > button {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    border-radius: 4px;
    letter-spacing: 0.3px;
    transition: all 0.15s ease;
}

.stButton > button[kind="primary"] {
    background-color: #FF6A00;
    border: none;
    color: #0E1117;
    font-weight: 600;
}

.stButton > button[kind="primary"]:hover {
    background-color: #E05E00;
}

.stButton > button[kind="secondary"] {
    background-color: transparent;
    border: 1px solid #1E2530;
    color: #8B949E;
}

.stButton > button[kind="secondary"]:hover {
    border-color: #FF6A00;
    color: #FF6A00;
}

/* ── Example question buttons ───────────────────────────────────────── */
.example-btn {
    display: block;
    width: 100%;
    text-align: left;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    background: #161B22;
    border: 1px solid #1E2530;
    border-radius: 5px;
    color: #8B949E;
    padding: 0.55rem 0.75rem;
    margin-bottom: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.example-btn:hover {
    border-color: #FF6A00;
    color: #C9D1D9;
    background: rgba(255, 106, 0, 0.05);
}

/* ── Expander (source chunks panel) ─────────────────────────────────── */
[data-testid="stExpander"] {
    background: #0D1117;
    border: 1px solid #1E2530;
    border-radius: 6px;
}

[data-testid="stExpander"] summary {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #6E7681;
}

/* Hide Streamlit's material icon text — it renders as literal
   "keyboard_arrow_right/down" without the font loaded */
[data-testid="stIconMaterial"] {
    display: none !important;
}

/* ── Metrics ────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #161B22;
    border: 1px solid #1E2530;
    border-radius: 6px;
    padding: 0.7rem;
}

[data-testid="stMetric"] label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6E7681;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.2rem;
    color: #FF6A00;
}

/* ── Dividers ───────────────────────────────────────────────────────── */
hr {
    border-color: #1E2530;
}

/* ── Scrollbar ──────────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #0E1117;
}

::-webkit-scrollbar-thumb {
    background: #1E2530;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #2D333B;
}

/* ── Hide streamlit defaults ────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ── Empty state ────────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #6E7681;
}

.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 0.8rem;
}

.empty-state-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    color: #8B949E;
    margin-bottom: 0.4rem;
}

.empty-state-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    color: #6E7681;
    max-width: 420px;
    margin: 0 auto;
    line-height: 1.5;
}

/* ── Pipeline diagram ───────────────────────────────────────────────── */
.pipeline-flow {
    display: flex;
    flex-direction: column;
    gap: 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.2rem 0;
}

.pipeline-row {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 0;
}

.pipeline-node {
    background: #161B22;
    border: 1px solid #1E2530;
    border-radius: 3px;
    padding: 2px 8px;
    color: #8B949E;
    white-space: nowrap;
}

.pipeline-node.active {
    border-color: #FF6A00;
    color: #FF6A00;
    background: rgba(255, 106, 0, 0.06);
}

.pipeline-connector {
    color: #2D333B;
    font-size: 0.7rem;
    padding-left: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "agent_memory" not in st.session_state:
    st.session_state.agent_memory = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "total_latency" not in st.session_state:
    st.session_state.total_latency = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
CITATION_PATTERN = re.compile(r"\[source:\s*([A-Z]{1,5}_chunk_\d+)\]")


def parse_citations(text: str):
    """Extract citation IDs and return clean text + list of citations."""
    citations = CITATION_PATTERN.findall(text)
    clean = CITATION_PATTERN.sub("", text).strip()
    clean = re.sub(r"\s{2,}", " ", clean)
    seen = []
    for c in citations:
        if c not in seen:
            seen.append(c)
    return clean, seen


def ask_agent(question: str):
    start = time.time()
    try:
        answer = run_agent(question, st.session_state.agent_memory)
    except Exception as e:
        err = str(e)
        # Corrupted message history — orphaned tool_call with no response.
        # Reset agent memory so the next query starts clean.
        if "tool_call_id" in err or "tool_calls" in err:
            st.session_state.agent_memory = {}
            st.error(
                "The agent hit a tool error on the previous query and the "
                "conversation history became corrupted. Session has been reset — "
                "please ask your question again."
            )
        else:
            st.error(f"Agent error: {err}")
        return
    elapsed = time.time() - start

    st.session_state.total_latency += elapsed
    st.session_state.query_count += 1

    clean_answer, citations = parse_citations(answer)

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "clean_content": clean_answer,
            "citations": citations,
            "latency": elapsed,
        }
    )


def render_message(msg):
    """Render a single chat message with citation cards."""
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            st.markdown(msg.get("clean_content", msg["content"]))

            citations = msg.get("citations", [])
            latency = msg.get("latency")

            if citations or latency:
                cols = st.columns([4, 1])

                if citations:
                    with cols[0]:
                        badges_html = "".join(
                            f'<span class="citation-badge">{c}</span>'
                            for c in citations
                        )
                        st.markdown(
                            f'<div class="citation-bar">{badges_html}</div>',
                            unsafe_allow_html=True,
                        )

                if latency is not None:
                    with cols[1]:
                        st.markdown(
                            f'<div style="text-align:right; font-family: JetBrains Mono, monospace; '
                            f'font-size: 0.65rem; color: #6E7681; padding-top: 0.95rem;">'
                            f"⏱ {latency:.1f}s</div>",
                            unsafe_allow_html=True,
                        )

            if citations:
                with st.expander(f"View {len(citations)} source chunk{'s' if len(citations) != 1 else ''}"):
                    st.markdown(
                        '<p style="font-size:0.75rem; color:#6E7681; margin-bottom:0.5rem;">'
                        "Chunk IDs referenced in this answer. To see full chunk text, "
                        "upgrade <code>run_agent</code> to return retrieved chunks.</p>",
                        unsafe_allow_html=True,
                    )
                    for c in citations:
                        parts = c.split("_chunk_")
                        ticker = parts[0] if len(parts) == 2 else "?"
                        chunk_n = parts[1] if len(parts) == 2 else c
                        st.markdown(
                            f'<div class="context-card" style="padding:0.5rem 0.7rem; margin-bottom:4px;">'
                            f'<span style="color:#FF6A00; font-family: JetBrains Mono, monospace; '
                            f'font-size:0.75rem; font-weight:600;">{ticker}</span>'
                            f'<span style="color:#2D333B; margin:0 6px;">|</span>'
                            f'<span style="color:#8B949E; font-family: JetBrains Mono, monospace; '
                            f'font-size:0.72rem;">chunk {chunk_n}</span></div>',
                            unsafe_allow_html=True,
                        )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
company = st.session_state.agent_memory.get("company", None)
ticker = st.session_state.agent_memory.get("ticker", None)

status_dot = "green" if ticker else "amber"
status_text = f"{ticker} LOADED" if ticker else "AWAITING QUERY"

st.markdown(
    f"""
    <div class="header-bar">
        <div>
            <div class="header-title">EARNINGS RESEARCH AGENT</div>
            <div class="header-subtitle">Agentic RAG · SEC 10-Q Filings · Semantic Search</div>
        </div>
        <div class="header-status">
            <span><span class="status-dot {status_dot}"></span> {status_text}</span>
            <span>QUERIES {st.session_state.query_count}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    # ── Active context ──
    st.markdown('<div class="sidebar-section-title">Active Context</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""<div class="context-card">
                <div class="context-label">Company</div>
                <div class="context-value {'active' if company else ''}">{company or '—'}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="context-card">
                <div class="context-label">Ticker</div>
                <div class="context-value {'active' if ticker else ''}">{ticker or '—'}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Session stats ──
    st.markdown('<div class="sidebar-section-title">Session</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.metric("Queries", st.session_state.query_count)
    with s2:
        avg = (
            st.session_state.total_latency / st.session_state.query_count
            if st.session_state.query_count
            else 0
        )
        st.metric("Avg Latency", f"{avg:.1f}s")

    # ── Pipeline ──
    st.markdown('<div class="sidebar-section-title">Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        """<div class="pipeline-flow">
            <div class="pipeline-row"><span class="pipeline-node">① Query</span></div>
            <div class="pipeline-row"><span class="pipeline-connector">↓</span><span class="pipeline-node">② Agent (gpt-4o-mini)</span></div>
            <div class="pipeline-row"><span class="pipeline-connector">↓</span><span class="pipeline-node">③ index_document</span></div>
            <div class="pipeline-row"><span class="pipeline-connector">↓</span><span class="pipeline-node">④ search_knowledge_base</span></div>
            <div class="pipeline-row"><span class="pipeline-connector">↓</span><span class="pipeline-node active">⑤ Answer + Citations</span></div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Supported companies ──
    st.markdown(
        '<div class="sidebar-section-title">Supported Companies</div>',
        unsafe_allow_html=True,
    )
    pills_html = ""
    for key, (name, tk) in COMPANY_TO_TICKER.items():
        active = "active" if tk == ticker else ""
        pills_html += f'<span class="company-pill {active}">{tk}</span>'
    st.markdown(f'<div class="company-grid">{pills_html}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Example queries ──
    st.markdown(
        '<div class="sidebar-section-title">Example Queries</div>',
        unsafe_allow_html=True,
    )

    examples = [
        ("Revenue breakdown", "What was Apple's revenue last quarter?"),
        ("Risk factors", "What are the red flags in Tesla's latest 10-Q?"),
        ("Follow-up", "How does that compare to Services revenue?"),
        ("Cross-company", "What was NVIDIA's net income?"),
        ("Out-of-scope test", "When was the US founded?"),
    ]
    for label, q in examples:
        if st.button(f"{label}", key=f"ex_{label}", use_container_width=True):
            ask_agent(q)
            st.rerun()

    st.markdown("---")

    if st.button("⟳  Clear Session", use_container_width=True):
        st.session_state.agent_memory = {}
        st.session_state.messages = []
        st.session_state.query_count = 0
        st.session_state.total_latency = 0.0
        st.rerun()

    # ── Tech stack ──
    st.markdown(
        '<div class="sidebar-section-title">Stack</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div style="font-family: JetBrains Mono, monospace; font-size: 0.65rem; color: #6E7681; line-height: 1.7;">
        LLM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; gpt-4o-mini<br>
        Embeddings &nbsp; text-embedding-3-small<br>
        Vector DB &nbsp;&nbsp; ChromaDB<br>
        Source &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; SEC EDGAR 10-Q<br>
        Framework &nbsp;&nbsp; No LangChain — built from scratch
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
if st.session_state.messages:
    for msg in st.session_state.messages:
        render_message(msg)
else:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">⬡</div>
            <div class="empty-state-title">Ready to research</div>
            <div class="empty-state-text">
                Ask a question about any supported company's latest 10-Q filing.
                The agent will fetch the SEC filing, index it, and answer with
                source citations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Input area
# ---------------------------------------------------------------------------
st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
prompt = st.text_area(
    "Question",
    placeholder="e.g. What were Apple's red flags in their latest 10-Q?",
    height=90,
    label_visibility="collapsed",
)
col1, col2 = st.columns([6, 1])
with col2:
    submit = st.button("Ask →", type="primary", use_container_width=True, disabled=not (prompt and prompt.strip()))
if submit and prompt.strip():
    with st.spinner("Agent is researching the filing..."):
        ask_agent(prompt.strip())
    st.rerun()
