from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages
import openai
import os

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set")

openai.api_key = api_key

app = Flask(__name__)

app.secret_key = "A1ntN0k3yL1k34S3cR3tK3y"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['GET', 'POST'])
def ask_gpt():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if not user_input:
            flash("Please enter your question", "error")
            return redirect(url_for('ask_gpt'))

        try:
            # Call OpenAI's new API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )

            gpt_response = response['choices'][0]['message']['content']
            return render_template('response.html', user_input="hello", gpt_response=gpt_response)

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for('ask_gpt'))

    return render_template('ask.html')

if __name__ == '__main__':
    app.run(debug=True)