"""Website lead agent: answers from site content, checks service area, books a slot.
LangGraph loop over Gemini function calling. Demo business is fictional."""
import os, sys, time, json
sys.stdout.reconfigure(encoding="utf-8")
from typing import TypedDict
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

C = {"dim": "\033[2m", "teal": "\033[38;5;37m", "yel": "\033[33m", "bold": "\033[1m", "end": "\033[0m"}

SITE = {
    "services": "We repair leaks, replace water heaters and clear blocked drains. Same-week visits.",
    "pricing": "Call-out fee is 49 EUR, waived if you book the repair. Water heater replacement from 650 EUR.",
    "areas": "We cover postcodes 01100 to 01400.",
}

def search_site(query: str) -> dict:
    """Search the business website pages for an answer."""
    hits = {k: v for k, v in SITE.items() if any(w in v.lower() or w in k for w in query.lower().split())}
    return {"pages": hits or SITE}

def check_service_area(postcode: str) -> dict:
    """Check whether a postcode is inside the service area."""
    n = int("".join(ch for ch in postcode if ch.isdigit()) or 0)
    return {"postcode": postcode, "covered": 1100 <= n <= 1400}

def book_slot(day: str, name: str) -> dict:
    """Book a visit slot and send the lead to the owner's calendar and CRM."""
    return {"booked": True, "day": day, "time": "10:00", "lead_sent_to": ["calendar", "crm"], "name": name}

TOOLS = {f.__name__: f for f in (search_site, check_service_area, book_slot)}
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
CFG = types.GenerateContentConfig(
    tools=list(TOOLS.values()),
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    system_instruction="You are the website assistant for a plumbing company. Answer only from search_site results, "
                       "check the postcode before booking, and keep replies to two short sentences.")

class State(TypedDict):
    contents: list
    done: bool

def agent(state: State) -> State:
    r = client.models.generate_content(model="gemini-3.8-flash", contents=state["contents"], config=CFG)
    msg = r.candidates[0].content
    state["contents"].append(msg)
    calls = [p.function_call for p in msg.parts if p.function_call]
    if not calls:
        print(f"{C['teal']}{C['bold']}agent ›{C['end']} {r.text.strip()}\n")
    return {"contents": state["contents"], "done": not calls}

def tools(state: State) -> State:
    parts = []
    for p in state["contents"][-1].parts:
        if p.function_call:
            fc = p.function_call
            print(f"{C['yel']}  tool  {fc.name}({json.dumps(dict(fc.args))}){C['end']}")
            out = TOOLS[fc.name](**fc.args)
            print(f"{C['dim']}        → {json.dumps(out)}{C['end']}")
            time.sleep(0.4)
            parts.append(types.Part.from_function_response(name=fc.name, response=out))
    state["contents"].append(types.Content(role="user", parts=parts))
    return {"contents": state["contents"], "done": False}

g = StateGraph(State)
g.add_node("agent", agent)
g.add_node("tools", tools)
g.set_entry_point("agent")
g.add_conditional_edges("agent", lambda s: END if s["done"] else "tools")
g.add_edge("tools", "agent")
app = g.compile()

if __name__ == "__main__":
    history = []
    for q in sys.argv[1:]:
        print(f"{C['bold']}visitor ›{C['end']} {q}")
        time.sleep(0.6)
        history.append(types.Content(role="user", parts=[types.Part(text=q)]))
        history = app.invoke({"contents": history, "done": False})["contents"]
