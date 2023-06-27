from pymongo import MongoClient
from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import random

load_dotenv()

# MongoDB connection configuration
mongo_url = os.environ.get('MONGODB_URL')
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB'] 
collection = db['messages']

# Message handler
def match_partner(update: Update, context):

    context.bot.send_message(chat_id=update.effective_chat.id, text="Matching you with a partner now...")
    # Getting user details
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    # Find the chat partner
    partnerid = user['partnerid']
    # Resetting any existing partner
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None}})

    # Unmatching the existing partner
    if partnerid is not None:
        # Add to recorded partners
        collection.update_one({'userid': userid}, {'$set': {f'pastPartners.{partnerid}': datetime.now()}})
        collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None, f'pastPartners.{userid}': datetime.now()}})
        context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /match for a new partner!")

    # Matching the user with the next available partner
    data = collection.find()
    # Getting most updated user details
    user = collection.find_one({'userid': userid})
    pastPartners = user['pastPartners']
    tempPartners = []
    matched = False
    finalPartner = None
    for item in data:
        # logic to determine the suitable happiness level of chat partner
        # happy match with sad (Comment out temporarily)
        # condition = int(item['happiness']) <= 5 if int(user['happiness']) > 5 else int(item['happiness']) > 5
        # Filtering out those with partners and own user ID
        if item['partnerid'] is None and item['userid'] != user['userid'] and item['userid'] not in user['reportedUsers']:
            itemPartner = item['userid']
            # If time difference less than 1 day
            if str(itemPartner) in pastPartners and datetime.now() - pastPartners[str(itemPartner)] <= timedelta(days=1):
                tempPartners.append(itemPartner)
            else:
                collection.update_one({'userid': userid}, {'$set': {'partnerid': itemPartner}})
                collection.update_one({'userid': itemPartner}, {'$set': {'partnerid': userid}})
                matched = True
                finalPartner = itemPartner
                break
    if not matched:
        print(tempPartners)
        if tempPartners == []:
            context.bot.send_message(chat_id=update.effective_chat.id, text="No users available at the moment. Please try again later!")
            return ConversationHandler.END
        randomPartner = random.choice(tempPartners)
        collection.update_one({'userid': userid}, {'$set': {'partnerid': randomPartner}})
        collection.update_one({'userid': randomPartner}, {'$set': {'partnerid': userid}})
        finalPartner = randomPartner    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matched! Say hi to your partner! If at any point your partner does not make you feel comfortable, you can report them by using /report!")
    context.bot.send_message(chat_id=finalPartner, text="Matched! Say hi to your partner! If at any point your partner does not make you feel comfortable, you can report them by using /report!")
    return

def end_chat(update: Update, context):
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    partnerid = user['partnerid']
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None, f'pastPartners.{partnerid}': datetime.now()}})
    collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None, f'pastPartners.{userid}': datetime.now()}})
    context.bot.send_message(chat_id=userid, text="Conversation cancelled. Please use /match for a new partner!")
    context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /match for a new partner!")
    return ConversationHandler.END

def handle_message(update: Update, context):
    message = update.message.text
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    if user is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your account has not been created yet. Please use the command /start to create first!")
        return ConversationHandler.END
    partnerid = user['partnerid']
    if partnerid is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have not been matched yet. Please use the command /match to get matched first!")
        return ConversationHandler.END
    else:
        print("MY PARTNER:" + str(partnerid))
        context.bot.send_message(chat_id=partnerid, text=user['nickname'] + ": " + message)
        print("MESSAGE SEND")

# Define conversation handler for /start command
chat_handler = ConversationHandler(
    entry_points=[CommandHandler('chat', match_partner)],
    states={},
    fallbacks=[MessageHandler(Filters.text, handle_message)],
)

end_handler = CommandHandler("end", end_chat)

message_handler = MessageHandler(Filters.text, handle_message)

