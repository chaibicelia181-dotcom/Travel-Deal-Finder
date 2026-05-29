"""
Travel Deal Finder Agent

An AI agent that uses tool use (function calling) to search for travel deals,
analyse prices, and recommend the best option with reasoning.

Architecture of the Agent:
  - Flask web server (routes + UI)
  - Groq API (llama3-groq-70b) as the AI agent brain
  - Tool use loop: the LLM decides which tools to call, we execute them, feed results back
  - Tools: search_flights, search_hotels, analyse_prices, get_destination_info

"""

import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))



TOOLS = [
    {
        "name": "search_flights",
        "description": (
            "Search for available flights to a destination. Returns a list of flight options "
            "with airlines, prices, duration, and availability. Use this to find current flight deals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "Destination city or airport code"},
                "departure_date": {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD format"},
                "origin": {"type": "string", "description": "Origin city, defaults to London"},
            },
            "required": ["destination", "departure_date", "return_date"],
        },
    },
    {
        "name": "search_hotels",
        "description": (
            "Search for available hotels at a destination. Returns hotel options with star ratings. "
            "Use this to find accommodation deals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "Destination city"},
                "check_in": {"type": "string", "description": "Check-in date in YYYY-MM-DD format"},
                "check_out": {"type": "string", "description": "Check-out date in YYYY-MM-DD format"},
                "guests": {"type": "integer", "description": "Number of guests, defaults to 2"},
            },
            "required": ["destination", "check_in", "check_out"],
        },
    },
    {
        "name": "analyse_prices",
        "description": (
            "Analyse pricing trends for a destination. Returns whether prices are currently "
            "above or below average, best time to book, and a value score. "
            "Use this to give the user pricing intelligence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "Destination city"},
                "travel_month": {"type": "string", "description": "Month of travel e.g. July"},
            },
            "required": ["destination", "travel_month"],
        },
    },
    {
        "name": "get_destination_info",
        "description": (
            "Get key travel information about a destination: weather, local tips, "
            "popular attractions, and travel advisories. Use this to enrich the recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "Destination city or country"},
            },
            "required": ["destination"],
        },
    },
]



# Tools Implementation: simulated data
# real APIs are used such as Amadeus, Booking.com, or Skyscanner


def search_flights(destination, departure_date, return_date, origin="London"):
    #Simulates a flight search API response.
    random.seed(hash(destination + departure_date))
    airlines = ["British Airways", "easyJet", "Ryanair", "Wizz Air", "Jet2", "TUI Airways"]
    results = []
    base_prices = {"barcelona": 89, "paris": 65, "rome": 110, "amsterdam": 75, "lisbon": 95,
                   "dubai": 340, "new york": 420, "cancun": 510, "tenerife": 130, "maldives": 780}
    base = next((v for k, v in base_prices.items() if k in destination.lower()), 150)

    for i in range(4):
        airline = airlines[i % len(airlines)]
        price = round(base * random.uniform(0.85, 1.35), 2)
        duration_h = random.randint(2, 12)
        duration_m = random.choice([0, 15, 30, 45])
        stops = 0 if price > base * 1.1 else random.choice([0, 0, 1])
        results.append({
            "airline": airline,
            "price_per_person_gbp": price,
            "outbound_duration": f"{duration_h}h {duration_m}m",
            "stops": stops,
            "seats_remaining": random.randint(2, 18),
            "departure_time": f"{random.randint(6,20):02d}:{random.choice(['00','15','30','45'])}",
        })
    results.sort(key=lambda x: x["price_per_person_gbp"])
    return {"origin": origin, "destination": destination, "departure_date": departure_date,
            "return_date": return_date, "flights": results}


def search_hotels(destination, check_in, check_out, guests=2):
    #Simulates a hotel search API response
    random.seed(hash(destination + check_in))
    hotel_names = {
        "barcelona": ["Hotel Arts Barcelona", "W Barcelona", "Barceló Raval", "Hotel Granados 83"],
        "paris": ["Hôtel du Louvre", "Le Marais Boutique", "Hotel Barrière", "Citadines Apart'hotel"],
        "rome": ["Hotel de Russie", "Portrait Roma", "Borghese Palace", "Hotel Artemide"],
    }
    generic = ["Grand Hotel Plaza", "City Centre Suites", "Boutique Harbour Inn",
               "The Meridian", "Comfort Select Hotel"]
    names = hotel_names.get(destination.lower(), generic)

    check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (check_out_dt - check_in_dt).days

    results = []
    for i, name in enumerate(names[:4]):
        stars = random.choice([3, 3, 4, 4, 5])
        price_per_night = round(random.uniform(60, 280) * (stars / 3), 2)
        results.append({
            "name": name,
            "stars": stars,
            "price_per_night_gbp": price_per_night,
            "total_gbp": round(price_per_night * nights, 2),
            "nights": nights,
            "rating": round(random.uniform(7.5, 9.8), 1),
            "amenities": random.sample(["Pool", "Spa", "Free WiFi", "Gym", "Restaurant",
                                        "Bar", "Concierge", "Room Service"], k=random.randint(3, 6)),
            "availability": random.choice(["Available", "Available", "Only 2 rooms left"]),
        })
    results.sort(key=lambda x: x["price_per_night_gbp"])
    return {"destination": destination, "check_in": check_in, "check_out": check_out,
            "guests": guests, "hotels": results}


def analyse_prices(destination, travel_month):
    #Simulates a pricing intelligence and trend analysis response
    random.seed(hash(destination + travel_month))
    peak_months = ["July", "August", "December", "June"]
    is_peak = travel_month in peak_months
    vs_average = random.uniform(15, 35) if is_peak else random.uniform(-25, 5)
    value_score = round(random.uniform(4.5, 7.0) if is_peak else random.uniform(7.0, 9.5), 1)
    return {
        "destination": destination,
        "travel_month": travel_month,
        "price_vs_annual_average_pct": round(vs_average, 1),
        "is_peak_season": is_peak,
        "value_score_out_of_10": value_score,
        "recommendation": (
            "Prices are above average — consider travelling shoulder season for better value."
            if is_peak else
            "Good time to travel — prices are at or below annual average."
        ),
        "best_booking_window": "4–6 weeks in advance" if is_peak else "2–4 weeks in advance",
        "price_trend": "Rising" if is_peak else random.choice(["Stable", "Falling slightly"]),
    }


def get_destination_info(destination):
    #Returns destination travel information.
    info = {
        "barcelona": {
            "weather_summary": "Warm Mediterranean climate. July/August hot (28–32°C). Spring/Autumn ideal.",
            "highlights": ["Sagrada Família", "Park Güell", "Las Ramblas", "Gothic Quarter", "Barceloneta Beach"],
            "tips": ["Book Sagrada Família tickets in advance", "Metro is cheap and reliable",
                     "Dinner is typically after 9pm", "Pickpocket hotspots around Las Ramblas"],
            "visa_required_uk": False,
            "currency": "Euro (€)",
            "language": "Catalan / Spanish",
        },
        "paris": {
            "weather_summary": "Mild. Spring (Apr-Jun) and Autumn (Sep-Oct) are best. Summers warm ~25°C.",
            "highlights": ["Eiffel Tower", "Louvre", "Montmartre", "Seine River Cruise", "Versailles"],
            "tips": ["Museum Pass saves money", "Metro is extensive", "Tipping not obligatory",
                     "Book popular restaurants ahead"],
            "visa_required_uk": False,
            "currency": "Euro (€)",
            "language": "French",
        },
    }
    generic = {
        "weather_summary": "Check local forecasts before travel.",
        "highlights": ["City centre exploration", "Local cuisine", "Cultural sites", "Day trips"],
        "tips": ["Check FCDO travel advice", "Take travel insurance", "Keep copies of documents"],
        "visa_required_uk": "Check FCDO website",
        "currency": "Check XE.com for current rates",
        "language": "Check local information",
    }
    data = info.get(destination.lower(), generic)
    data["destination"] = destination
    return data



# Tool Dispatcher: It routes The LLM's tool call requests to real functions


def execute_tool(tool_name, tool_input):
    dispatch = {
        "search_flights": search_flights,
        "search_hotels": search_hotels,
        "analyse_prices": analyse_prices,
        "get_destination_info": get_destination_info,
    }
    fn = dispatch.get(tool_name)
    if fn:
        return fn(**tool_input)
    return {"error": f"Unknown tool: {tool_name}"}


# This is the Agent loop, it keeps running until the LLM stops calling tools and delivers a final answer

def run_agent(destination, departure_date, return_date, budget=None):
    """
    1. Send user request + tools to the LLM (Groq/Llama3)
    2. If the LLM returns tool calls, execute each tool
    3. Feed results back to the LLM as tool_result messages
    4. Repeat until the LLM returns a final text response (no more tool calls)

    """
    budget_text = f" My total budget is approximately £{budget} per person." if budget else ""

    messages = [
        {
            "role": "user",
            "content": (
                f"I'm looking for a travel deal from the UK to {destination}. "
                f"I want to travel from {departure_date} to {return_date}.{budget_text} "
                f"Please search for flights and hotels, analyse whether prices are good value right now, "
                f"and get destination information. Then give me a clear, friendly recommendation "
                f"of the best overall deal with your reasoning. Format your final answer with "
                f"clear sections: Best Flight, Best Hotel, Price Analysis, Destination Tips, "
                f"and Overall Recommendation."
            ),
        }
    ]

    tool_calls_log = []  # track what the agent did

    # Agentic loop
    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            tools=[{"type": "function", "function": {**t, "parameters": t["input_schema"]}} for t in TOOLS],
            messages=messages,
        )

        # Collect any tool calls made this turn

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            return {"answer": message.content, "tool_calls": tool_calls_log}
        tool_results = []
        for tc in tool_calls:
            args = json.loads(tc.function.arguments)
            tool_calls_log.append({"tool": tc.function.name, "input": args})
            result = execute_tool(tc.function.name, args)
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })
        messages.append({"role": "assistant", "tool_calls": tool_calls, "content": ""})
        messages.extend(tool_results)



#Define flask routes:

@app.route("/")
def index():
    today = datetime.today()
    default_depart = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    default_return = (today + timedelta(days=37)).strftime("%Y-%m-%d")
    return render_template("index.html",
                           default_depart=default_depart,
                           default_return=default_return)

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    destination = data.get("destination", "").strip()
    departure_date = data.get("departure_date", "")
    return_date = data.get("return_date", "")
    budget = data.get("budget", "")

    if not destination or not departure_date or not return_date:
        return jsonify({"error": "Please fill in all required fields."}), 400

    try:
        result = run_agent(destination, departure_date, return_date, budget or None)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
