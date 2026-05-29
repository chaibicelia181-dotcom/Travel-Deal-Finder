# Travel Deal Finder AI Agent

A Python Flask web application that uses **AI Agent architecture** (tool use / function calling) to autonomously search for travel deals, analyse prices, and recommend the best option.

## What Makes This an "AI Agent"

Unlike a simple chatbot that follows a fixed script, this project uses **agentic tool use**:

1. The user submits a destination and dates
2. The LLM (Groq/Llama3) autonomously decides which tools to call and in what order
3. The agent calls actual functions: search_flights, search_hotels, analyse_prices, get_destination_info
4. Results are fed back to the LLM, which continues reasoning
5. The loop repeats until the LLM has enough information to give a final recommendation



## Tech Stack

Web framework: Flask |
AI Agent: Groq API (llama-3.3-70b-versatile) |
Agent pattern: Tool use, function calling loop |
Frontend | HTML5, CSS3, JavaScript |
Data simulation: Python (random seed for reproducible results) |



## Setup & Running

### 1. Install dependencies
```bash
pip install flask groq python-dotenv
```

### 2. Run
```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.


## Extending This Project

Ideas to take this further:
- Replace simulated data with Amadeus API (flights) and Booking.com API (hotels)
- Store searches in SQLite to track price trends over time 
- **User accounts**: Add Flask-Login to save favourite searches
- Deploy to AWS 
