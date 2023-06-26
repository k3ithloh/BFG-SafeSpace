from pymongo import MongoClient
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, filters, MessageHandler, Updater, CallbackQueryHandler
from modules.createUser import conversation_handler
from modules.chatModule import chat_handler, message_handler
from modules.reportUser import report_handler
from dotenv import load_dotenv
import os
load_dotenv()

def main():
    telebotToken = os.environ.get('TELETOKEN')

    # Create the Telegram bot instance
    updater = Updater(token=telebotToken, use_context=True)
    dispatcher = updater.dispatcher

    # Add the handlers to the dispatcher ORDER OF HANDLERS MATTER
    dispatcher.add_handler(report_handler) 
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(chat_handler)
    dispatcher.add_handler(message_handler)
    
    # Start the bot
    updater.start_polling()

if __name__ == '__main__':
    main()
