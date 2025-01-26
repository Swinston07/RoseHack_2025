from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_scss import Scss
import markdown
import requests
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
HERE_API_ID = os.getenv("HERE_API_ID")
HERE_API_KEY = os.getenv("HERE_API_KEY")

if not HERE_API_KEY:
    raise ValueError("HERE API Key is not set")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

openai.api_key = api_key

app = Flask(__name__)
app.secret_key = "A1ntN0k3yL1k34S3cR3tK3y"

# Compile SCSS dynamically (not recommended for production)
Scss(app, static_dir="static", asset_dir="assets")


def get_conversation():
    """Retrieve or initialize the conversation session."""
    if "conversation" not in session:
        session["conversation"] = [
            {"role": "system", "content": "You are a helpful assistant for mothers."}
        ]
    return session["conversation"]


@app.route("/", methods=["GET", "POST"])
def home():
    """Handle the main route for conversation and user input."""
    conversation = get_conversation()

    if request.method == "POST":
        user_input = request.form.get("user_input")
        user_lat = request.form.get("latitude")
        user_lon = request.form.get("longitude")

        if not user_input:
            flash("Please enter your question.", "error")
            return redirect(url_for("home"))

        try:
            conversation.append({"role": "user", "content": user_input})

            # GPT-4 interaction
            response = openai.ChatCompletion.create(
                model="gpt-4", messages=conversation
            )

            if "choices" in response and len(response["choices"]) > 0:
                model_response = response["choices"][0]["message"]["content"]
            else:
                model_response = "I'm sorry, I couldn't process your request."

            # Determine location category for user queries
            location_category = None
            if user_lat and user_lon:
                try:
                    lat = float(user_lat)
                    lon = float(user_lon)
                except ValueError:
                    flash("Invalid coordinates provided.", "error")
                    return redirect(url_for("home"))

                intent_query = f"""
                Based on the user's input: '{user_input}', identify if it requires location-based suggestions 
                (e.g., restaurants, parks, cafes) with 30 miles of the user. If it does, return the most relevant one-word category. 
                Otherwise, return 'none'.
                """
                intent_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant helping mothers with ideas (e.g., events, plans, self-care) to make life easier.",
                        },
                        {"role": "user", "content": intent_query},
                    ],
                )
                location_category = (
                    intent_response["choices"][0]["message"]["content"].strip().lower()
                )

            # Fetch nearby places using HERE API if category and coordinates are available
            if user_lat and user_lon and location_category != "none":
                here_results = fetch_nearby_places(lat, lon, location_category)
                if here_results and "items" in here_results:
                    model_response += f"\n\nHere are some nearby {location_category}:\n"
                    for item in here_results["items"]:
                        model_response += f"- {item['title']} ({item['address']['label']})\n"
                else:
                    model_response += (
                        f"\n\nSorry, I couldn't find any nearby {location_category}."
                    )

            # Convert response to Markdown
            conversation.append(
                {"role": "assistant", "content": markdown.markdown(model_response)}
            )
            session["conversation"] = conversation

        except openai.error.AuthenticationError:
            flash("Authentication error with OpenAI API. Please check your API key.", "error")
        except openai.error.RateLimitError:
            flash("Rate limit exceeded. Please try again later.", "error")
        except openai.error.APIConnectionError:
            flash("Network error with OpenAI API. Check your connection.", "error")
        except openai.error.OpenAIError as e:
            flash(f"OpenAI API error: {e}", "error")

    # Render the template if the request method is GET
    return render_template(
        "index.html",
        conversation=[
            message for message in conversation if message["role"] != "system"
        ],
    )


def fetch_nearby_places(lat, lon, query):
    """Fetch nearby places using the HERE Places API."""
    url = "https://discover.search.hereapi.com/v1/discover"
    params = {
        "at": f"{lat},{lon}",
        "q": query,
        "apiKey": HERE_API_KEY,
        "limit": 5,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching places from HERE API: {e}")
        return {}


@app.route("/clear")
def clear_conversation():
    """Clear the conversation session."""
    session.pop("conversation", None)
    flash("Conversation cleared.", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
