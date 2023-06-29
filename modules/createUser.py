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

# User Configuration
user = {
    "_id": None,
    "userid": None, # used to identify user and retrieve data from db on user
    "student": None, # future: if not student then its a counsellor 
    "nickname": None, 
    "gender": None,
    "happiness": None,
    "partnerid": None,
    "available": False,
    "ageRange": None,
    "challenge": None,
    "reportedUsers": [],
    "pastPartners": {},
}

# Setting conversation states
START, STUDENTQN, GENDERQN, NAMEQN, HAPPINESSQN, CONTROLLERHANDLER, AGEQN, CHALLENGEQN = range(8)

# # Conversation state history
# state_history = []

# Start command handler
def start(update, context):
    # state_history.clear()  # Clear state history when starting account change
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello there! Welcome to SafeSpace 💆‍♂️💆‍♀️🏠, we are here to help you with all of your mental health related queries 😊. Please rest assured that in accordance with Singapore's Personal Data Protection Act, we will not be collecting any of your personal data. You can create your new account using /setup")
    return ConversationHandler.END

def controller(update, context):
    collection = db['messages']
    checkUser = collection.find_one({'userid': update.effective_chat.id})
    if checkUser is None:
        insertUser = user
        insertUser['userid'] = update.effective_chat.id
        insertUser['_id'] = update.effective_chat.id
        collection.insert_one(
            insertUser
        )
        checkUser = insertUser
    keyboard = [
        [InlineKeyboardButton(f"Gender {'✅' if checkUser['gender'] is not None else ''}", callback_data='gender'),
        InlineKeyboardButton(f"Student {'✅' if checkUser['student'] is not None else ''}", callback_data='student')],
        [InlineKeyboardButton(f"Nickname {'✅' if checkUser['nickname'] is not None else ''}", callback_data='nickname'),
        InlineKeyboardButton(f"Happiness {'✅' if checkUser['happiness'] is not None else ''}", callback_data='happiness')],
        [InlineKeyboardButton(f"Age Range {'✅' if checkUser['ageRange'] is not None else ''}", callback_data='ageRange'),
        InlineKeyboardButton(f"Challenge {'✅' if checkUser['challenge'] is not None else ''}", callback_data='challenge')],
        [InlineKeyboardButton("Complete", callback_data='complete')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Let us begin setting up your account!', reply_markup=reply_markup)
    return CONTROLLERHANDLER

def control_handler(update, context):
    query = update.callback_query
    chosen_option = query.data
    if chosen_option == 'gender':
        gender_keyboard = [
            [InlineKeyboardButton("Male", callback_data='Male')],
            [InlineKeyboardButton("Female", callback_data='Female')],
            [InlineKeyboardButton("Prefer not to share", callback_data='NA')],
        ]
        gender_markup = InlineKeyboardMarkup(gender_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nWhat is your gender?', reply_markup=gender_markup, parse_mode='MarkdownV2')
        return GENDERQN
    
    if chosen_option == 'student':
        student_keyboard = [
            [InlineKeyboardButton("Yes", callback_data='Yes')],
            [InlineKeyboardButton("No", callback_data='No')],
        ]
        student_markup = InlineKeyboardMarkup(student_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nAre you a student?', reply_markup=student_markup, parse_mode='MarkdownV2')
        return STUDENTQN
    
    if chosen_option == 'nickname':
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nPlease enter a nickname that you would like to be addressed by\. Or type "NA" if you prefer not to say\.', parse_mode='MarkdownV2')
        return NAMEQN
    
    if chosen_option == 'happiness':
        happiness_keyboard = [
            [InlineKeyboardButton("1", callback_data='1'),
            InlineKeyboardButton("2", callback_data='2'),
            InlineKeyboardButton("3", callback_data='3'),
            InlineKeyboardButton("4", callback_data='4'),
            InlineKeyboardButton("5", callback_data='5')],
            [InlineKeyboardButton("6", callback_data='6'),
            InlineKeyboardButton("7", callback_data='7'),
            InlineKeyboardButton("8", callback_data='8'),
            InlineKeyboardButton("9", callback_data='9'),
            InlineKeyboardButton("10", callback_data='10')],
            [InlineKeyboardButton("Prefer not to say", callback_data='NA')],
        ]
        happiness_markup = InlineKeyboardMarkup(happiness_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nOn a scale of 1 \- 10, how would you rate how happy you are lately?', reply_markup=happiness_markup, parse_mode='MarkdownV2')
        return HAPPINESSQN
    
    if chosen_option == 'ageRange':
        age_keyboard = [
            [InlineKeyboardButton("<15", callback_data=0)],
            [InlineKeyboardButton("16-18", callback_data=1)],
            [InlineKeyboardButton("19-21", callback_data=2)],
            [InlineKeyboardButton("22-25", callback_data=3)],
            [InlineKeyboardButton(">25", callback_data=4)]
        ]
        age_markup = InlineKeyboardMarkup(age_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nWhat is your age range?', reply_markup=age_markup, parse_mode='MarkdownV2')
        return AGEQN
    
    if chosen_option == 'challenge':
        challenge_keyboard = [
            [InlineKeyboardButton("Family", callback_data="family"),
            InlineKeyboardButton("Social Life", callback_data="social")],
            [InlineKeyboardButton("Academics", callback_data="academics"),
            InlineKeyboardButton("Others", callback_data="others")],
            [InlineKeyboardButton("NA", callback_data="NA")]
        ]
        challenge_markup = InlineKeyboardMarkup(challenge_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'__*{chosen_option.capitalize()}*__\n\nWhat is the biggest challenge that you are facing now?', reply_markup=challenge_markup, parse_mode='MarkdownV2')
        return CHALLENGEQN
    
    if chosen_option == 'complete':
        collection = db['messages']
        userComplete = collection.find_one({'userid': update.effective_chat.id})
        if userComplete['gender'] is not None and userComplete['happiness'] is not None and userComplete['nickname'] is not None and userComplete['student'] is not None and userComplete['ageRange'] is not None and userComplete['challenge'] is not None:
            return handle_completed(update, context)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Please complete all fields before completing.')
            return controller(update, context)


def handle_studentqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'student': chosen_option}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)


def handle_genderqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'gender': chosen_option}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)

def handle_nameqn(update, context):
    givenNickname = update.message.text.strip()
    if givenNickname == '/cancel':
        cancel(update, context)
        return ConversationHandler.END
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'nickname': givenNickname}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)

def handle_happinessqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'happiness': chosen_option}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)

def handle_ageqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'ageRange': chosen_option}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)

def handle_challengeqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    collection = db['messages']
    collection.update_one({'userid': update.effective_chat.id}, {'$set': {'challenge': chosen_option}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)
    
def handle_completed(update, context):
    # user['userid'] = update.effective_user.id
    # Because i cannot put < > into f strings
    lessthan = "\<"
    morethan = "\>"
    collection = db['messages']
    finUser = collection.find_one({'userid': user['userid']})
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"__*Completed*__\n\nAccount updated successfully\!\n\nUser ID: {finUser['userid']}\nStudent: {finUser['student']}\nNickname: {finUser['nickname']}\nGender: {finUser['gender']}\nHappiness: {finUser['happiness']} \nAge Range: {lessthan + '15' if finUser['ageRange'] == 0 else '16-18' if finUser['ageRange'] == 1 else '19-21' if finUser['ageRange'] == 2 else '22-25' if finUser['ageRange'] == 3 else morethan + '25'}\nChallenge: {finUser['challenge']}", parse_mode='MarkdownV2')
    context.bot.send_message(chat_id=update.effective_chat.id, text="Try to find a match now with /begin!")
    # # Adding to DB
    # collection = db['messages']
    # checkUser = collection.find_one({'userid': user['userid']})
    # # Resetting user variable
    # if checkUser is not None:
    #     user['pastPartners'] = checkUser['pastPartners']
    #     user['reportedUsers'] = checkUser['reportedUsers']
    #     user['partnerid'] = checkUser['partnerid']
    # collection.update_one({'userid': user['userid']}, {'$set': user}, upsert=True)
    # user['userid'] = None
    # user['student'] = None
    # user['nickname'] = None
    # user['gender'] = None
    # user['happiness'] = None
    # user['pastPartners'] = {}
    # user['reportedUsers'] = []
    # user['partnerid'] = None
    # user['ageRange'] = None
    # user['challenge'] = None
    return ConversationHandler.END

def reset(update, context):
    collection = db['messages']
    collection.update_one(
        {'userid': update.effective_chat.id}, 
            {'$set': 
                {
                    "student": None,
                    "nickname": None, 
                    "gender": None,
                    "happiness": None,
                    "ageRange": None,
                    "challenge": None,
                }
            }
    )
    # Resetting user variable
    # user['userid'] = None
    # user['student'] = None
    # user['nickname'] = None
    # user['gender'] = None
    # user['happiness'] = None
    # user['pastPartners'] = {}
    # user['reportedUsers'] = []
    # user['partnerid'] = None
    # user['ageRange'] = None
    # user['challenge'] = None
    # if checkUser is not None:
    #     user['pastPartners'] = checkUser['pastPartners']
    #     user['reportedUsers'] = checkUser['reportedUsers']
    #     user['partnerid'] = checkUser['partnerid']
    context.bot.send_message(chat_id=update.effective_chat.id, text='Account setup reset.')
    return ConversationHandler.END


creation_handler = ConversationHandler(
    entry_points=[CommandHandler('setup', controller),],
    states={
        CONTROLLERHANDLER: [CallbackQueryHandler(control_handler)],
        STUDENTQN: [CallbackQueryHandler(handle_studentqn)],
        GENDERQN: [CallbackQueryHandler(handle_genderqn)],
        NAMEQN: [MessageHandler(Filters.text, handle_nameqn)],
        HAPPINESSQN: [CallbackQueryHandler(handle_happinessqn)],
        AGEQN: [CallbackQueryHandler(handle_ageqn)],
        CHALLENGEQN: [CallbackQueryHandler(handle_challengeqn)],
        
    },
    fallbacks=[CommandHandler("reset", reset)],
)

start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={        
    },
    fallbacks=[],
)



