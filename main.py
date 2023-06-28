from telegram.ext import Updater
from modules.createUser import start_handler, creation_handler
from modules.chatModule import chat_handler, message_handler, end_handler
from modules.reportUser import report_handler
from modules.deleteUser import delete_handler
from modules.viewUser import view_handler
from dotenv import load_dotenv
import os
load_dotenv()

def main():
    telebotToken = os.environ.get('TELETOKEN')

    # Create the Telegram bot instance
    updater = Updater(token=telebotToken, use_context=True)
    dispatcher = updater.dispatcher

    # Add the handlers to the dispatcher ORDER OF HANDLERS MATTER
    dispatcher.add_handler(view_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(report_handler) 
    dispatcher.add_handler(end_handler)
    dispatcher.add_handler(creation_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(chat_handler)
    dispatcher.add_handler(message_handler)
    
    # Start the bot
    updater.start_polling()

if __name__ == '__main__':
    main()
