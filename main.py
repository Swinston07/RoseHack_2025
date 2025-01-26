from flask import Flask, request, render_template, render_template_string, redirect, url_for, flash, session
from flask_scss import Scss
import markdown

import openai
import os

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

openai.api_key = api_key

app = Flask(__name__)
app.secret_key = "A1ntN0k3yL1k34S3cR3tK3y"

# Compile SCSS dynamically (not recommended for production)
Scss(app, static_dir='static', asset_dir='assets')

def get_conversation():
    if "conversation" not in session:
        session["conversation"] = [
            {"role": "system", "content": "You are a helpful assistant for mothers."}
        ]
    return session["conversation"]

@app.route('/', methods=['GET', 'POST'])
def home():
    conversation = get_conversation()

    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if not user_input:
            flash("Please enter your question.", "error")
            return redirect(url_for('home'))

        try:
            conversation.append({"role": "user", "content": user_input})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation
            )

            model_response = response['choices'][0]['message']['content']

            model_response_html = markdown.markdown(model_response)

            conversation.append({"role": "assistant", "content": model_response_html})

            session['conversation'] = conversation

        except openai.error.OpenAIError as e:
            flash(f"OpenAI API error: {e}", "error")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "error")

    display_conversation = [
        message for message in conversation if message["role"] != "system"
    ]

    return render_template('index.html', conversation=display_conversation)

@app.route('/clear')
def clear_conversation():
    session.pop("conversation", None)
    flash("Conversation cleared.", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)