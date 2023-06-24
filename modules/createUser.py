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
    "userid": None,
    "student": None,
    "name": None,
    "gender": None,
    "happiness": None,
    'partnerid': None,
}

# Setting conversation states
START, STUDENTQN, GENDERQN, NAMEQN, HAPPINESSQN = range(5)


# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello there! Welcome to SafeSpace 💆‍♂️💆‍♀️🏠, we are here to help you with all of your mental health related queries 😊.Please rest assured that in accordance with Singapore's Personal Data Protection Act, we will not be collecting any of your personal data.")
    user['userid'] = update.effective_user.id
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, could I find out more information about you. Are you a Student?")
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="Before we begin, I would like to collect some information from you.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Let's begin! May i know your gender?")
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
    user['name'] = studentQuestion
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next question. On a scale of 1 - 10, how would you rate how happy you are lately? Please enter a whole number from 1 to 10 or 'NA' if you are not comfortable sharing")
    keyboard = [
        [InlineKeyboardButton("1", callback_data='1')],
        [InlineKeyboardButton("2", callback_data='2')],
        [InlineKeyboardButton("3", callback_data='3')],
        [InlineKeyboardButton("4", callback_data='4')],
        [InlineKeyboardButton("5", callback_data='5')],
        [InlineKeyboardButton("6", callback_data='6')],
        [InlineKeyboardButton("7", callback_data='7')],
        [InlineKeyboardButton("8", callback_data='8')],
        [InlineKeyboardButton("9", callback_data='9')],
        [InlineKeyboardButton("10", callback_data='10')],
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
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Account created successfully!\n\nUser ID: {user['userid']}\nStudent: {'Yes' if user['student'] else 'No'}\nName: {user['name']}\nGender: {user['gender']}\nHappiness: {user['happiness']}")
    # Adding to DB
    collection = db['messages']
    collection.insert_one(user)
    return ConversationHandler.END
    
# start_handler = CommandHandler('start', start)

# Cancel command handler (optional)
def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Conversation canceled.')
    return ConversationHandler.END

# Command to store data in MongoDB
def store_data(update, context):
    user_id = update.effective_user.id
    message_text = update.message.text

    # Store data in MongoDB
    collection = db['messages']
    collection.insert_one({'user_id': user_id, 'message': message_text})

    context.bot.send_message(chat_id=update.effective_chat.id, text='Data stored successfully.')

store_data_handler = CommandHandler('store', store_data)

# Command to retrieve data from MongoDB
def retrieve_data(update, context):
    user_id = update.effective_user.id

    # Retrieve data from MongoDB
    collection = db['messages']
    result = collection.find({'user_id': user_id})

    messages = [doc['message'] for doc in result]
    response = '\n'.join(messages)

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

retrieve_data_handler = CommandHandler('retrieve', retrieve_data)

# Create Conversation Handler
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        STUDENTQN: [CallbackQueryHandler(handle_studentqn)],
        GENDERQN: [CallbackQueryHandler(handle_genderqn)],
        NAMEQN: [MessageHandler(Filters.text, handle_nameqn)],
        HAPPINESSQN: [CallbackQueryHandler(handle_happinessqn)]
    },
    fallbacks=[MessageHandler(Filters.command, cancel)],
)