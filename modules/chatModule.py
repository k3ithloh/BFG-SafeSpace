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
    checkUser = collection.find_one({'userid': update.effective_user.id})
    if checkUser is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your account has not been created yet. Please use the command /setup to create first!")
        return ConversationHandler.END
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matching you with a partner now...")
    # Getting user details
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    # Set user avaiability to true and update database
    collection.update_one({'userid': userid}, {'$set': {'available': True}})
    # Find the chat partner
    partnerid = user['partnerid']
    # Resetting any existing partner
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None}})

    # Unmatching the existing partner
    if partnerid is not None:
        # Add to recorded partners
        collection.update_one({'userid': userid}, {'$set': {f'pastPartners.{partnerid}': datetime.now()}})
        collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None, f'pastPartners.{userid}': datetime.now()}})
        context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /begin for a new partner!")

    # Matching the user with the next available partner
    data = collection.aggregate([
        {
            '$addFields': {
                'happiness_numeric': {
                    '$cond': {
                        'if': { '$eq': ['$happiness', 'NA'] },
                        'then': -1,  # Assign a lower value for 'NA'
                        'else': { '$toInt': '$happiness' }  # Convert other values to numeric
                    }
                }
            }
        },
        { '$sort': { 'happiness_numeric': -1 } }  # Sort by 'happiness_numeric' field in descending order
    ])
    # Getting most updated user details
    user = collection.find_one({'userid': userid})
    userHappiness = int(user['happiness'])
    pastPartners = user['pastPartners']
    secondPartners = []
    firstPartners = []
    NAPartners = []
    finalPartner = None
    for item in data:
        # logic to determine the suitable happiness level of chat partner
        # Filtering out those with partners and own user ID
        if (item['partnerid'] is None) and (item['userid'] != user['userid']) and (item['userid'] not in user['reportedUsers']) and (item['available'] == True):
            itemPartner = item['userid']
            # If time difference less than 1 day (Lower priority group)
            if str(itemPartner) in pastPartners and datetime.now() - pastPartners[str(itemPartner)] <= timedelta(days=1):
                secondPartners.append(itemPartner)
            elif item['happiness_numeric'] == -1: # NA Happiness group
                NAPartners.append(itemPartner)
            else:
                firstPartners.append((itemPartner, item['happiness_numeric']))

    # If there are any possible users in the priority group, use them
    if len(firstPartners) != 0:
        print("First priority group is:" + firstPartners)
        # first partners are already sorted from highest to lowest
        max_difference = float('-inf')
        max_difference_user = None
        for partnerid, partnerHappiness in firstPartners:
            difference = abs(partnerHappiness - userHappiness)
            if difference > max_difference:
                max_difference = difference
                max_difference_user = partnerid
        collection.update_one({'userid': userid}, {'$set': {'partnerid': max_difference_user}})
        collection.update_one({'userid': max_difference_user}, {'$set': {'partnerid': userid}})
        finalPartner = max_difference_user

    # If there are any possible users in the lower priority group, use them
    if len(firstPartners) == 0 and len(secondPartners) != 0:
        print("Second priority group is:" + secondPartners)
        randomPartner = random.choice(secondPartners)
        collection.update_one({'userid': userid}, {'$set': {'partnerid': randomPartner}})
        collection.update_one({'userid': randomPartner}, {'$set': {'partnerid': userid}})
        finalPartner = randomPartner 

    # If there are any possible users in the NA priority group, use them
    if len(firstPartners) == 0 and len(secondPartners) == 0 and len(NAPartners) != 0: 
        print("NA priority group is:" + NAPartners)
        randomPartner = random.choice(NAPartners)
        collection.update_one({'userid': userid}, {'$set': {'partnerid': randomPartner}})
        collection.update_one({'userid': randomPartner}, {'$set': {'partnerid': userid}})
        finalPartner = randomPartner 

    # No possible users to match with at all
    if len(firstPartners) == 0 and len(secondPartners) == 0 and len(NAPartners) == 0: 
        context.bot.send_message(chat_id=update.effective_chat.id, text="No users available at the moment. Please try again later!")
        # collection.update_one({'userid': userid}, {'$set': {'available': False}})
        return ConversationHandler.END   
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matched! Say hi to your partner! If at any point your partner does not make you feel comfortable, you can report them by using /report!")
    context.bot.send_message(chat_id=finalPartner, text="Matched! Say hi to your partner! If at any point your partner does not make you feel comfortable, you can report them by using /report!")
    return

def end_chat(update: Update, context):
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    partnerid = user['partnerid']
    collection.update_one({'userid': userid}, {'$set': {'available': False}})
    collection.update_one({'userid': partnerid}, {'$set': {'available': False}})
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None, f'pastPartners.{partnerid}': datetime.now()}})
    collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None, f'pastPartners.{userid}': datetime.now()}})
    context.bot.send_message(chat_id=userid, text="Conversation cancelled. Please use /begin for a new partner!")
    context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /begin for a new partner!")
    return ConversationHandler.END

def handle_message(update: Update, context):
    message = update.message.text
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    if user is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your account has not been created yet. Please use the command /setup to create first!")
        return ConversationHandler.END
    partnerid = user['partnerid']
    if partnerid is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have not been matched yet. Please use the command /begin to get matched first!")
        return ConversationHandler.END
    else:
        print("MY PARTNER:" + str(partnerid))
        context.bot.send_message(chat_id=partnerid, text=user['nickname'] + ": " + message)
        print("MESSAGE SEND")

# Define conversation handler for /begin command
chat_handler = ConversationHandler(
    entry_points=[CommandHandler('begin', match_partner)],
    states={},
    fallbacks=[],
)

end_handler = CommandHandler("end", end_chat)

message_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.text, handle_message)],
    states={},
    fallbacks=[],
)

