import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from test.rag_chain import load_rag_chain, get_answer

load_dotenv()

# Initialize Slack app
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

# Load RAG chain once at startup
print("Loading KnowBot RAG engine...")
chain_tuple = load_rag_chain()
print("KnowBot Slack bot is ready!")

# Fires when someone @mentions the bot in a channel
@app.event("app_mention")
def handle_mention(event, say):
    # Remove the @KnowBot part from the question
    user_question = event["text"].split(">")[-1].strip()
    user_id = event["user"]

    if not user_question:
        say(f"<@{user_id}> Please ask me a question after mentioning me!")
        return

    # Get answer from RAG chain
    answer, sources, _ = get_answer(chain_tuple, user_question)
    source_text = " | ".join(sources) if sources else "Company documents"

    # Send formatted reply
    say(blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{user_id}>\n\n{answer}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":file_folder: *Sources:* {source_text}"
                }
            ]
        }
    ])

# Fires when someone DMs the bot directly
@app.event("message")
def handle_dm(event, say):
    # Ignore messages from bots to avoid loops
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return

    user_question = event.get("text", "").strip()
    if not user_question:
        return

    answer, sources, _ = get_answer(chain_tuple, user_question)
    source_text = " | ".join(sources) if sources else "Company documents"

    say(blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": answer
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":file_folder: *Sources:* {source_text}"
                }
            ]
        }
    ])

# Start the bot
if __name__ == "__main__":
    print("Starting KnowBot Slack integration...")
    handler = SocketModeHandler(
        app,
        os.getenv("SLACK_APP_TOKEN")
    )
    handler.start()