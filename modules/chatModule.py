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
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matching you with a partner now...")

    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None}})
    # Find the chat partner
    partnerid = user['partnerid']

    # Unmatching the existing partner
    if partnerid is not None:
        collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None}})
        context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /match for a new partner!")

    # Matching the user with the next available partner
    for item in data:
        if item['partnerid'] is None and item['userid'] != user['userid']:
            partnerid = item['userid']
            collection.update_one({'userid': userid}, {'$set': {'partnerid': partnerid}})
            collection.update_one({'userid': partnerid}, {'$set': {'partnerid': userid}})
            break
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matched! If at any point your partner does not make you feel comfortable, you can report them by using /report!")
    return


def handle_message(update: Update, context):
    message = update.message.text
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    partnerid = user['partnerid']
    if partnerid is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have not been matched yet. Please use the command /match to get matched first!")
    else:
        context.bot.send_message(chat_id=partnerid, text=message)

# Define conversation handler for /start command
chat_handler = ConversationHandler(
    entry_points=[CommandHandler('match', match_partner)],
    states={},
    fallbacks=[MessageHandler(Filters.text, handle_message)]
)

message_handler = MessageHandler(Filters.text, handle_message)
