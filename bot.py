from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Handler for the /start command
def start(update: Update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Hello! I am your Telegram bot.")

# Handler for text messages
def handle_message(update: Update, context):
    message_text = update.message.text
    response_text = f"You said: {message_text}"
    context.bot.send_message(chat_id=update.message.chat_id, text=response_text)

def main():
    # Create the Telegram Bot updater
    updater = Updater("6274496403:AAGehEhKyVAGNOQ8c75y8Y5DE-Muu9x1w50", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))

    # Register message handler
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
