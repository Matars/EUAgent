# EU Database Assistant

This is a Streamlit application that demonstrates OpenAI's function calling capabilities to query a mock EU database.

## Features

- Chat interface with AI assistant
- Function calling to fetch EU data:
  - EU regulations on various topics
  - Statistics for EU countries
  - Information about EU institutions

## Setup Instructions

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI and Europeana API keys to the `.env` file

## Running the Application

Start the application with:

```
streamlit run app.py
```

The app will open in your default web browser.

## Example Queries

Try asking the assistant questions like:

- "What are the EU regulations on digital services?"
- "Tell me the statistics for Germany"
- "Which EU institutions are located in Brussels?"
- "What is the European Parliament responsible for?"
- "What's the GDP of France?"

## How It Works

The application demonstrates OpenAI's function calling feature by:

1. Defining mock EU database functions
2. Allowing the model to decide when to call these functions
3. Executing the function calls to retrieve mock EU data
4. Providing the results back to the model
5. Displaying the final response with the incorporated data

## Technologies Used

- Python
- Streamlit
- OpenAI API
- Mock EU database (simulated data)
