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
    'partnerid': None,
    "reportedUsers": [],
    "pastPartners": {},
}

# Setting conversation states
START, STUDENTQN, GENDERQN, NAMEQN, HAPPINESSQN = range(5)


# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello there! Welcome to SafeSpace 💆‍♂️💆‍♀️🏠, we are here to help you with all of your mental health related queries 😊.Please rest assured that in accordance with Singapore's Personal Data Protection Act, we will not be collecting any of your personal data.")
    user['userid'] = update.effective_user.id
    # Add in existing user logic here
    context.bot.send_message(chat_id=update.effective_chat.id, text="Before we begin, I would like to collect some information from you. If at any point you wish to stop, use the /cancel to stop the process.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Let's begin! First I would like to know if you are you a Student?")
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='Yes')],
        [InlineKeyboardButton("No", callback_data='No')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Are you Student?', reply_markup=reply_markup)
    return STUDENTQN

def handle_studentqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['student'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next, may i know your gender?")
    keyboard = [
        [InlineKeyboardButton("Male", callback_data='Male')],
        [InlineKeyboardButton("Female", callback_data='Female')],
        [InlineKeyboardButton("Not comfortable sharing", callback_data='NA')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='What is your gender?', reply_markup=reply_markup)
    return GENDERQN


def handle_genderqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['gender'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next question. May i know your Name? Please enter your name or 'NA' if you are not comfortable sharing")
    return NAMEQN

def handle_nameqn(update, context):
    studentQuestion = update.message.text.strip()
    user['nickname'] = studentQuestion
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next question. On a scale of 1 - 10, how would you rate how happy you are lately? Please enter a whole number from 1 to 10 or 'NA' if you are not comfortable sharing")
    keyboard = [
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='What is your current happiness level?', reply_markup=reply_markup)
    return HAPPINESSQN

def handle_happinessqn(update, context):
    query = update.callback_query
    chosen_option = query.data
    user['happiness'] = chosen_option
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Account created successfully!\n\nUser ID: {user['userid']}\nStudent: {'Yes' if user['student'] else 'No'}\nNickname: {user['nickname']}\nGender: {user['gender']}\nHappiness: {user['happiness']}")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Try to find a match now with /match! Or you can wait for someone to match you as well.")

    # Adding to DB
    collection = db['messages']
    collection.insert_one(user)
    return ConversationHandler.END
    

# Cancel command handler (optional)
def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Account setup canceled.')
    return ConversationHandler.END


# Create Conversation Handler
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        STUDENTQN: [CallbackQueryHandler(handle_studentqn)],
        GENDERQN: [CallbackQueryHandler(handle_genderqn)],
        NAMEQN: [MessageHandler(Filters.text, handle_nameqn)],
        HAPPINESSQN: [CallbackQueryHandler(handle_happinessqn)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)