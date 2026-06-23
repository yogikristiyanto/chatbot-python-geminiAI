from flask import Flask, render_template, request, Response
import google.generativeai as genai
from config import GEMINI_API_KEY
from db import SessionLocal, Conversation

app = Flask(__name__)
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Create a local config.py or set the environment variable."
    )
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash"
)


@app.route("/", methods=["GET", "POST"])
def index():
    response_text = ""
    if request.method == "POST":
        prompt = request.form["prompt"]
        response = model.generate_content(prompt)
        response_text = response.text

        # Simpan riwayat percakapan ke database
        db = SessionLocal()
        try:
            conv = Conversation(user_message=prompt, bot_response=response_text)
            db.add(conv)
            db.commit()
        finally:
            db.close()

    return render_template(
        "index.html",
        response=response_text
    )


@app.route("/history")
def history():
    db = SessionLocal()
    try:
        items = db.query(Conversation).order_by(Conversation.timestamp.desc()).all()
    finally:
        db.close()
    return render_template("history.html", conversations=items)


@app.route("/export")
def export_csv():
    db = SessionLocal()
    try:
        items = db.query(Conversation).order_by(Conversation.timestamp.desc()).all()
    finally:
        db.close()

    import csv
    from io import StringIO

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["id", "timestamp", "user_message", "bot_response"])
    for c in items:
        writer.writerow([c.id, c.timestamp.isoformat(), c.user_message, c.bot_response])

    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=chat_history.csv"})


if __name__ == "__main__":
    app.run(debug=True)