from tools import download_earnings_report, index_document, search_knowledge_base
from openai import OpenAI
import json


COMPANY_TO_TICKER = {
    "apple": ("Apple", "AAPL"),
    "nvidia": ("NVIDIA", "NVDA"),
    "microsoft": ("Microsoft", "MSFT"),
    "tesla": ("Tesla", "TSLA"),
    "amazon": ("Amazon", "AMZN"),
}


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the indexed earnings report. Use a specific query that preserves the user's financial metric, period, and comparison terms. For example, use 'revenue latest quarter three months ended' instead of just 'revenue'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "ticker": {
                        "type": "string", 
                        "description": "The stock ticker symbol e.g. AAPL"
                    }
                },
                "required": ["query", "ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "index_document",
            "description": "Download and index the latest 10-Q earnings report for a ticker. Call this before searching if the document hasn't been indexed yet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol e.g. AAPL"
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]


def resolve_company(question):
    question_lower = question.lower()
    for company_key, company_info in COMPANY_TO_TICKER.items():
        if company_key in question_lower:
            return company_info
    return None


def get_ticker_for_question(question, session_state):
    resolved_company = resolve_company(question)
    if resolved_company:
        company, ticker = resolved_company
        session_state["company"] = company
        session_state["ticker"] = ticker
        return company, ticker

    if session_state.get("ticker"):
        return session_state.get("company"), session_state["ticker"]

    return None, None


def run_agent(question, session_state):
    company, ticker = get_ticker_for_question(question, session_state)
    if not ticker:
        return "Please mention one of these companies: Apple, NVIDIA, Microsoft, Tesla, or Amazon."

    client = OpenAI()
    
    system_prompt = [
                {"role": "system", "content": 
            "You are a financial research assistant. "
            "Always index the document before searching if not already indexed. "
            "Only answer using retrieved chunks, and if chunks don't contain relevant info, "
            "say what you searched for and that the earnings report does not contain that information. "
            "DONT USE OUTSIDE KNOWLEDGE. "
            "Answer only the question asked. Do not add extra comparisons, trends, or metrics unless the user asks for them. "
            "When you answer, cite the chunk IDs you used as [source: AAPL_chunk_42] at the end of each claim. "
            "For every number you mention, cite the chunk that contains that exact number. "
            "If one sentence uses numbers from multiple chunks, cite all relevant chunk IDs."
                }
            ]
    
    if "messages" not in session_state:
        session_state["messages"] = system_prompt
    messages = session_state["messages"]
    messages.append({"role": "user", "content": f"{question} (company:{company}, ticker:{ticker})..."})

    tool_map ={
            "index_document" : index_document,
            "search_knowledge_base": search_knowledge_base
            }

    while True:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages, 
            tools=tools
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "stop":
            messages.append(message)  # add final answer to history
            session_state["messages"] = messages  # save before returning
            return message.content
        elif finish_reason == "tool_calls":
            messages.append(message)
            for tool_call in message.tool_calls:
                name = tool_call.function.name #the tool LLM wants to call 
                args = json.loads(tool_call.function.arguments) #the arguments, parsed from JSON into python dictionary 
                print(f"Agent calling: {name} with {args}")
                result = tool_map[name](**args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": format_tool_result(name, result)
                })

def format_tool_result(name, result):
    if name == "search_knowledge_base":
        formatted_chunks = []
        for chunk in result:
            formatted_chunks.append(
                f"[source: {chunk['id']}]\n{chunk['text']}"
            )
        return "\n\n".join(formatted_chunks)
    return str(result)

if __name__ == '__main__':
    #answer = run_agent("When was the US founded?", "NVDA") 
    # leaks outside knowledge when queries are out of scope, and the fix is constraining the system prompt to only allow answers grounded in retrieved context.
    #answer = run_agent("What's the total cumulative revenue of Apple in the last 3 months", "AAPL")
    #session_state = {}
    #answer = run_agent("What are the red flags in Tesla's latest 10-Q", session_state)
    #print(answer)
    #follow_up = run_agent("What about net income?", session_state)
    #print(follow_up)
    #print(session_state)
    session_state = {}
    answer = run_agent("What was Apple's iPhone revenue?", session_state)
    print(answer)
    follow_up = run_agent("How does that compare to Services revenue?", session_state)
    print(follow_up)