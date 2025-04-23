# Europeana Database Assistant

This is a Streamlit application that demonstrates OpenAI's function calling capabilities to query Europeana's database via its APIs.

## Current features

-   Chat interface with AI assistant
-   Function calling to fetch Europeana's data:

## Planed

-   AI agent using tools to fetch Europeana's data with function calling.

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

Try asking the assistant whatever you like related to European Cultural Heritage or Europeana.

## How It Works

The application demonstrates OpenAI's function calling feature by:

1. Defining Europeana database functions
2. Allowing the model to decide when to call these functions
3. Executing the function calls to retrieve Europeana's data
4. Providing the results back to the model
5. Displaying the final response with the incorporated data

## Technologies Used

-   Python
-   Streamlit
-   OpenAI API
-   Europeana APIs
