# Website lead agent

A small agent that sits behind a website chat. It answers visitors from the site's own content,
checks whether they are inside the service area, and books a visit. The booking step is where a
real deployment would hand the lead to a calendar and a CRM.

It is built as a LangGraph loop over Gemini function calling: the model decides which tool to
call, the graph runs the tool, and the result goes back to the model until it can answer.

```
visitor › Do you replace water heaters, and what does it cost?
  tool  search_site({"query": "water heater replacement cost"})
agent › Yes, we replace water heaters with same-week visits available. Replacement starts
        from 650 EUR, with the 49 EUR call-out fee waived if you book the service.

visitor › I'm in 01250. Can someone come Thursday? I'm Dana.
  tool  check_service_area({"postcode": "01250"})
        → {"postcode": "01250", "covered": true}
  tool  book_slot({"day": "Thursday", "name": "Dana"})
        → {"booked": true, "day": "Thursday", "time": "10:00", "lead_sent_to": ["calendar", "crm"]}
agent › We confirmed your postcode is in our service area and booked your visit for Thursday at 10:00.
```

The business, prices and postcodes are made up for the demo.

## How it works

| Piece | What it does |
|---|---|
| `search_site` | Looks up the site's pages. In the demo this is a small dict; in a real build it is a search over the crawled site or a vector index. |
| `check_service_area` | Checks a postcode before anything is booked. |
| `book_slot` | Books the visit. In a real build this calls the calendar and CRM APIs. |
| Graph | `agent` node calls Gemini with the tools; `tools` node runs whatever it asked for; the loop ends when the model replies without a tool call. |

The system prompt tells the model to answer only from `search_site` results and to check the
postcode before booking, so it does not invent prices or book outside the area.

## Run it

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key        # PowerShell: $env:GEMINI_API_KEY="your_key"
python lead_agent.py "Do you replace water heaters?" "I'm in 01250. Can someone come Thursday? I'm Dana."
```

Each argument is one visitor message; the conversation history carries over between them.

## Where it goes next

- Swap the `SITE` dict for retrieval over the real website.
- Connect `book_slot` to Google Calendar or Cal.com and push the lead to HubSpot or Pipedrive.
- Put it behind a chat widget on WordPress or any site.

Author: Istiaque Ahmed (Ish)
