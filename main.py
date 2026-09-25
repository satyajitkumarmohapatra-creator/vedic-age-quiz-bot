
from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]
API = "https://api.telegram.org/bot" + TOKEN

QUESTIONS = [
    (
        "Which is the oldest Veda?",
        ["Samaveda", "Rigveda", "Yajurveda", "Atharvaveda"],
        1
    ),
    (
        "How many Mandalas are there in the Rigveda?",
        ["8", "9", "10", "12"],
        2
    ),
    (
        "Which Veda is mainly a collection of melodies and chants?",
        ["Samaveda", "Rigveda", "Atharvaveda", "Yajurveda"],
        0
    ),
    (
        "Which Veda contains charms, spells and healing prayers?",
        ["Rigveda", "Yajurveda", "Samaveda", "Atharvaveda"],
        3
    ),
    (
        "Which Veda deals mainly with sacrificial formulae?",
        ["Atharvaveda", "Samaveda", "Yajurveda", "Rigveda"],
        2
    )
]

users = {}

def telegram(method, data):
    return requests.post(
        API + "/" + method,
        json=data,
        timeout=30
    ).json()

def send_message(chat_id, text):
    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text
    })

def send_question(chat_id):
    user = users[chat_id]
    number = user["question"]

    if number >= len(QUESTIONS):
        score = user["score"]
        total = len(QUESTIONS)

        send_message(
            chat_id,
            "🎉 QUIZ COMPLETED!\n\n"
            f"Total: {total}\n"
            f"Correct: {score}\n"
            f"Wrong: {total - score}\n"
            f"Score: {score}/{total}\n"
            f"Percentage: {score * 100 / total:.2f}%"
        )
        return

    question, options, correct = QUESTIONS[number]

    result = telegram("sendPoll", {
        "chat_id": chat_id,
        "question": f"Q{number + 1}. {question}",
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": False
    })

    if result.get("ok"):
        users[chat_id]["poll_id"] = result["result"]["poll"]["id"]
        users[chat_id]["correct"] = correct

@app.route("/", methods=["GET"])
def home():
    return "Vedic Age Quiz Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text == "/start":
            users[chat_id] = {
                "question": 0,
                "score": 0,
                "poll_id": None,
                "correct": None
            }

            send_message(
                chat_id,
                "📚 VEDIC AGE QUIZ\n\n"
                "Test Quiz - 5 Questions\n\n"
                "Send /quiz to start."
            )

        elif text == "/quiz":
            if chat_id not in users:
                users[chat_id] = {
                    "question": 0,
                    "score": 0,
                    "poll_id": None,
                    "correct": None
                }

            send_question(chat_id)

    if "poll_answer" in data:
        answer = data["poll_answer"]

        for chat_id, user in users.items():
            if user["poll_id"] == answer["poll_id"]:

                if answer.get("option_ids"):
                    selected = answer["option_ids"][0]

                    if selected == user["correct"]:
                        user["score"] += 1

                user["question"] += 1
                user["poll_id"] = None

                send_question(chat_id)
                break

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
