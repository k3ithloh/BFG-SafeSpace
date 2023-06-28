from pymongo import MongoClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
import os
load_dotenv()

# MongoDB connection configuration
mongo_url = os.environ.get('MONGODB_URL')
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB']  # Replace 'your_database_name' with your desired database name
collection = db['messages']

def view_user(update, context):
    user = collection.find_one({'userid': update.effective_chat.id})
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"User account request successful!\n\nUser ID: {user['userid']}\nStudent: {'Yes' if user['student'] else 'No'}\nNickname: {user['nickname']}\nGender: {user['gender']}\nHappiness: {user['happiness']}")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"To edit your account use /setup!")

    return ConversationHandler.END

view_handler = CommandHandler('view', view_user)
