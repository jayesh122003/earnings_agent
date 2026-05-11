import os
import sys

import streamlit as st


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENT_DIR = os.path.join(ROOT_DIR, "agent")

if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from agent import run_agent


st.set_page_config(
    page_title="Financial Earnings Research Agent",
    layout="wide",
)


if "agent_memory" not in st.session_state:
    st.session_state.agent_memory = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "question" not in st.session_state:
    st.session_state.question = ""


def ask_agent(question):
    answer = run_agent(question, st.session_state.agent_memory)
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    return answer


st.title("Financial Earnings Research Agent")
st.caption("Ask questions about a company's latest 10-Q filing. The agent resolves the company, retrieves SEC filing chunks, and answers with sources.")


with st.sidebar:
    st.header("Current Context")

    company = st.session_state.agent_memory.get("company", "None")
    ticker = st.session_state.agent_memory.get("ticker", "None")

    st.write(f"Company: **{company}**")
    st.write(f"Ticker: **{ticker}**")

    if st.button("Clear memory"):
        st.session_state.agent_memory = {}
        st.session_state.messages = []
        st.session_state.question = ""
        st.rerun()

    st.header("Example Questions")

    examples = [
        "What was Tesla's revenue last quarter?",
        "What about net income?",
        "What are the risks in Tesla's latest 10-Q?",
        "When was the US founded?",
    ]

    for example in examples:
        if st.button(example):
            st.session_state.question = example


question = st.text_area(
    "Ask about a company's latest 10-Q",
    key="question",
    placeholder="Example: What was Apple's revenue last quarter?",
    height=110,
)

if st.button("Ask Agent", type="primary", disabled=not question.strip()):
    with st.spinner("Agent is researching the filing..."):
        ask_agent(question.strip())


st.divider()

if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
else:
    st.info("Ask a question to start. If your follow-up does not mention a company, the agent will reuse the current company context.")
