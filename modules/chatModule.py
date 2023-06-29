from pymongo import MongoClient
from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta
from googleapiclient import discovery


import os
import random
load_dotenv()

# MongoDB connection configuration
mongo_url = os.environ.get('MONGODB_URL')
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB'] 
collection = db['messages']

# Google Cloud API configuration
API_KEY = os.environ.get('API_KEY')
client = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey=API_KEY,
  discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery=False,
)

# Import badwords list
with open('badwords.txt', 'r') as f:
    bad_words = [word.strip().lower() for word in f.readlines()]

def check_profanity(text):
    analyze_request = {
        'comment': { 'text': text },
        'requestedAttributes': {'TOXICITY': {}}
    }
    response = client.comments().analyze(body=analyze_request).execute()
    score = response['attributeScores']['TOXICITY']['summaryScore']['value']
    return score > 0.70  # Change the threshold based on your requirements

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
                    '$toInt': '$happiness'  # Convert the 'happiness' field to an integer
                }
            }
        },
        { '$sort': { 'happiness_numeric': -1 } }  # Sort by 'happiness_numeric' field in descending order
    ])

    # Getting most updated user details
    user = collection.find_one({'userid': userid})
    # userHappiness = int(user['happiness'])
    pastPartners = user['pastPartners']
    secondPartners = []
    firstPartners = []
    # NAPartners = []
    finalPartner = None
    # userConcern = user['concern']
    # userAgeRange = user['ageRange']
    for item in data:
        # logic to determine the suitable happiness level of chat partner
        # Filtering out those with partners and own user ID
        if (item['partnerid'] is None) and (item['userid'] != user['userid']) and (item['userid'] not in user['reportedUsers']) and (item['available'] == True):
            itemPartner = item['userid']
            # If time difference less than 1 day (Lower priority group)
            if str(itemPartner) in pastPartners and datetime.now() - pastPartners[str(itemPartner)] <= timedelta(days=1):
                secondPartners.append(item)
            # elif item['happiness_numeric'] == -1: # NA Happiness group
            #     NAPartners.append(item)
            else:
                firstPartners.append(item)
    # If there are any possible users in the priority group, use them

    if len(firstPartners) != 0:
        finalPartner = matching_algo(firstPartners, user)

    # If there are any possible users in the lower priority group, use them
    if len(firstPartners) == 0 and len(secondPartners) != 0:
        finalPartner = matching_algo(secondPartners, user)

    # # If there are any possible users in the NA priority group, use them
    # if len(firstPartners) == 0 and len(secondPartners) == 0 and len(NAPartners) != 0: 
    #     finalPartner = matching_algo(NAPartners, user)

    # No possible users to match with at all
    if finalPartner == None: 
        context.bot.send_message(chat_id=update.effective_chat.id, text="No users available at the moment. We will match you soon once someone is available!")
        # collection.update_one({'userid': userid}, {'$set': {'available': False}})
        return ConversationHandler.END   
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Matched! You can now say hi to your partner in this chat! If at any point your partner does not make you feel comfortable, you can report them using /report!")
    context.bot.send_message(chat_id=finalPartner, text="Matched! You can now say hi to your partner in this chat! If at any point your partner does not make you feel comfortable, you can report them using /report!")
    return

def matching_algo(array, user):
    userHappiness = int(user['happiness'])
    userid = user['userid']
    userConcern = user['concern']
    userAgeRange = user['ageRange']
    sameConcern = []
    sameAgeRange = []
    currentArray = array
    for item in currentArray:
        if item['concern'] == userConcern:
            sameConcern.append(item)
    if len(sameConcern) != 0:
        currentArray = sameConcern
    for item in currentArray:
        if int(item['ageRange']) - 1 <= int(userAgeRange) <= int(item['ageRange']) + 1:
            sameAgeRange.append(item)
    if len(sameAgeRange) != 0:
        currentArray = sameAgeRange

    # first partners are already sorted from highest to lowest
    # max_difference = float('-inf')
    max_difference_user = None
    happiest = currentArray[0]
    saddest = currentArray[-1]
    if abs(userHappiness - happiest['happiness_numeric']) >= abs(userHappiness - saddest['happiness_numeric']):
        max_difference_user = happiest['userid']
    else:
        max_difference_user = saddest['userid']
    # for partner in currentArray:
    #     partnerHappiness = partner['happiness_numeric']
    #     partnerid = partner['userid']
    #     difference = abs(partnerHappiness - userHappiness)
    #     # Match partner if same issue
    #     if difference > max_difference:
    #         max_difference = difference
    #         max_difference_user = partnerid
    collection.update_one({'userid': userid}, {'$set': {'partnerid': max_difference_user}})
    collection.update_one({'userid': max_difference_user}, {'$set': {'partnerid': userid}})
    return max_difference_user


def end_chat(update: Update, context):
    userid = update.effective_user.id
    user = collection.find_one({'userid': userid})
    partnerid = user['partnerid']
    collection.update_one({'userid': userid}, {'$set': {'available': False}})
    collection.update_one({'userid': partnerid}, {'$set': {'available': False}})
    collection.update_one({'userid': userid}, {'$set': {'partnerid': None, f'pastPartners.{partnerid}': datetime.now()}})
    collection.update_one({'userid': partnerid}, {'$set': {'partnerid': None, f'pastPartners.{userid}': datetime.now()}})
    context.bot.send_message(chat_id=userid, text="Conversation cancelled. Please use /begin to look for a new partner!")
    context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /begin to look for a new partner!")
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
        # Check if the message contains any bad words
        if any(bad_word in message.lower() for bad_word in bad_words):
            try:
                # If the message contains a bad word, check it against the profanity API
                if check_profanity(message): 
                    # If the profanity API indicates the message is inappropriate, notify the sender
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Your message contains inappropriate content. Please mind your language.")
                else:
                    # If the profanity API indicates the message is okay, send it to the recipient
                   context.bot.send_message(chat_id=partnerid, text=user['nickname'] + ": " + message)
            except:  # ! catches rate limit exceptions as our Quota is 60 requests per minute
                context.bot.send_message(chat_id=update.effective_chat.id, text="Your message contains inappropriate content. Please mind your language.")
        else:
            # If the message does not contain any bad words, send it to the recipient
            context.bot.send_message(chat_id=partnerid, text=user['nickname'] + ": " + message)

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

