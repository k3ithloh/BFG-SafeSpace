from pymongo import MongoClient
from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
import os
load_dotenv()

# MongoDB connection configuration
mongo_url = os.environ.get('MONGODB_URL')
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB'] 
collection = db['messages']

data = collection.find()

# Message handler
def match_partner(update: Update, context):
    user_id = update.effective_user.id
    message = update.message.text

    # Find the chat partner
    user = collection.find_one({'userid': user_id})
    partner_id = user['partnerid']

    if partner_id is None:
        # No chat partner yet, pair the user with the next available partner
        for item in data:
            if item['partnerid'] is None and item['userid'] != user['userid']:
                partner_id = item['userid']
                collection.update_one({'userid': user_id}, {'$set': {'partnerid': partner_id}})
                break

def handle_message(update: Update, context):
    if partner_id is not None:
        # Forward the message to the chat partner
        context.bot.send_message(chat_id=partner_id, text=message)
    else:
        # No chat partner available
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, there are currently no available chat partners. Please try again later.")

# Define conversation handler for /start command
start_handler = ConversationHandler(
    entry_points=[CommandHandler('match', match_partner)],
    states={},
    fallbacks=[MessageHandler(Filters.text, handle_message)]
)