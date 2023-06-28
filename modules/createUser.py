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
    "userid": None, # used to identify user and retrieve data from db on user
    "student": None, # future: if not student then its a counsellor 
    "nickname": None, 
    "gender": None,
    "happiness": None,
    "partnerid": None,
    "available": False,
    "reportedUsers": [],
    "pastPartners": {},
}

# Setting conversation states
START, STUDENTQN, GENDERQN, NAMEQN, HAPPINESSQN, CONTROLLERHANDLER = range(6)

# # Conversation state history
# state_history = []

# Start command handler
def start(update, context):
    # state_history.clear()  # Clear state history when starting account change
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello there! Welcome to SafeSpace 💆‍♂️💆‍♀️🏠, we are here to help you with all of your mental health related queries 😊.Please rest assured that in accordance with Singapore's Personal Data Protection Act, we will not be collecting any of your personal data. You can create your new account using /setup")
    return ConversationHandler.END

def controller(update, context):
    keyboard = [
        [InlineKeyboardButton(f"Gender {'✅' if user['gender'] is not None else ''}", callback_data='gender'),
        InlineKeyboardButton(f"Student {'✅' if user['student'] is not None else ''}", callback_data='student')],
        [InlineKeyboardButton(f"Nickname {'✅' if user['nickname'] is not None else ''}", callback_data='nickname'),
        InlineKeyboardButton(f"Happiness {'✅' if user['happiness'] is not None else ''}", callback_data='happiness')],
        [InlineKeyboardButton("Complete", callback_data='complete')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Let us start setting up your account!', reply_markup=reply_markup)
    return CONTROLLERHANDLER

def control_handler(update, context):
    query = update.callback_query
    chosen_option = query.data
    context.bot.send_message(chat_id=update.effective_chat.id, text='You have chosen: ' + chosen_option)

    if chosen_option == 'gender':
        gender_keyboard = [
            [InlineKeyboardButton("Male", callback_data='Male')],
            [InlineKeyboardButton("Female", callback_data='Female')],
            [InlineKeyboardButton("Not comfortable sharing", callback_data='NA')],
        ]
        gender_markup = InlineKeyboardMarkup(gender_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text='What is your gender?', reply_markup=gender_markup)
        return GENDERQN
    if chosen_option == 'student':
        student_keyboard = [
            [InlineKeyboardButton("Yes", callback_data='Yes')],
            [InlineKeyboardButton("No", callback_data='No')],
        ]
        student_markup = InlineKeyboardMarkup(student_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Are you Student?', reply_markup=student_markup)
        return STUDENTQN
    if chosen_option == 'nickname':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter a nickname that you would like to be addressed by. Or type 'NA' if you are not comfortable sharing")
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
            [InlineKeyboardButton("Not comfortable sharing", callback_data='NA')],
        ]
        happiness_markup = InlineKeyboardMarkup(happiness_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text='On a scale of 1 - 10, how would you rate how happy you are lately?', reply_markup=happiness_markup)
        return HAPPINESSQN
    if chosen_option == 'complete':
        if user['gender'] is not None and user['happiness'] is not None and user['nickname'] is not None and user['student'] is not None:
            return handle_completed(update, context)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Please complete all fields before completing.')
            return controller(update, context)


def handle_studentqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['student'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)


def handle_genderqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['gender'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)

def handle_nameqn(update, context):
    studentQuestion = update.message.text.strip()
    if studentQuestion == '/cancel':
        cancel(update, context)
        return ConversationHandler.END
    user['nickname'] = studentQuestion
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    # track_conversation_history(update, context)
    return controller(update, context)

def handle_happinessqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['happiness'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    return controller(update, context)
    
def handle_completed(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Account updated successfully!\n\nUser ID: {user['userid']}\nStudent: {'Yes' if user['student'] else 'No'}\nNickname: {user['nickname']}\nGender: {user['gender']}\nHappiness: {user['happiness']}")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Try to find a match now with /begin!")
    # Adding to DB
    collection = db['messages']
    checkUser = collection.find_one({'userid': user['userid']})
    if checkUser is not None:
        user['pastPartners'] = checkUser['pastPartners']
        user['reportedUsers'] = checkUser['reportedUsers']
        user['partnerid'] = checkUser['partnerid']
    collection.update_one({'userid': user['userid']}, {'$set': user}, upsert=True)
    return ConversationHandler.END

# Cancel command handler (optional)
def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Account setup canceled.')
    return ConversationHandler.END


creation_handler = ConversationHandler(
    entry_points=[CommandHandler('setup', controller),],
    states={
        CONTROLLERHANDLER: [CallbackQueryHandler(control_handler)],
        STUDENTQN: [CallbackQueryHandler(handle_studentqn)],
        GENDERQN: [CallbackQueryHandler(handle_genderqn)],
        NAMEQN: [MessageHandler(Filters.text, handle_nameqn)],
        HAPPINESSQN: [CallbackQueryHandler(handle_happinessqn)],
        
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

start_handler = CommandHandler('start', start)



