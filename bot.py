from pymongo import MongoClient
from telegram import Bot
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, Updater
from dotenv import load_dotenv
import os
load_dotenv()
# Getting env variables
telebotToken = os.environ.get('TELETOKEN')
mongo_url = os.environ.get('MONGODB_URL')

# MongoDB connection configuration
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB']  # Replace 'your_database_name' with your desired database name

# Telegram bot configuration
bot_token = telebotToken  # Replace 'your_bot_token' with the actual bot token
bot = Bot(token=bot_token)

# User Configuration
user = {
    "userid": None,
    "student": None,
    "name": None,
    "gender": None,
    "happiness": None
}

# Setting conversation states
START, STUDENTQN, GENDERQN, NAMEQN, HAPPINESSQN = range(5)

# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello there! Welcome to SafeSpace 💆‍♂️💆‍♀️🏠, we are here to help you with all of your mental health related queries 😊.Please rest assured that in accordance with Singapore's Personal Data Protection Act, we will not be collecting any of your personal data.")
    user['userid'] = update.effective_user.id
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, could I find out more information about you. Are you a Student? Reply 'Y' for yes or 'N' for no")
    return STUDENTQN

    # context.bot.send_message(chat_id=update.effective_chat.id, text="Student status updated!")
def handle_studentqn(update, context):
    studentQuestion = update.message.text.strip()
    if studentQuestion == 'Y':
        user['student'] = True
    elif studentQuestion == 'N':
        user['student'] = False
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please respond with 'Y' for yes or 'N' for no")
        return STUDENTQN
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Before we begin, I would like to collect some information from you. At any time to can choose to say 'NA' if you are not comfortable sharing!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Let's begin! May i know your gender? Please reply 'M' for male, 'F' for female or 'NA' if you are not comfortable sharing")
    return GENDERQN

def handle_genderqn(update, context):
    studentQuestion = update.message.text.strip()
    if studentQuestion == 'M':
        user['gender'] = 'Male'
    elif studentQuestion == 'F':
        user['gender'] = 'Female'
    elif studentQuestion == 'NA':
        user['gender'] = 'NA'
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please respond with 'M' for male, 'F' for female or 'NA' if you are not comfortable sharing")
        return GENDERQN
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next question. May i know your Name? Please enter your name or 'NA' if you are not comfortable sharing")
    return NAMEQN

def handle_nameqn(update, context):
    studentQuestion = update.message.text.strip()
    if studentQuestion == '':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter a valid name")
        return NAMEQN
    else:
        user['name'] = studentQuestion
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Next question. On a scale of 1 - 10, how would you rate how happy you are lately? Please enter a whole number from 1 to 10 or 'NA' if you are not comfortable sharing")
    return HAPPINESSQN

def handle_happinessqn(update, context):
    studentQuestion = update.message.text.strip()
    if studentQuestion == 'NA':
        user['happiness'] = "NA"
    else:
        if studentQuestion.isdigit() and 1 <= int(studentQuestion) <= 10:
            user['happiness'] = studentQuestion
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter a whole number from 1 to 10 or 'NA' if you are not comfortable sharing")
            return HAPPINESSQN
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for updating!")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Account created successfully!\n\nUser ID: {user['userid']}\nStudent: {'Yes' if user['student'] else 'No'}\nName: {user['name']}\nGender: {user['gender']}\nHappiness: {user['happiness']}")
    # Adding to DB
    collection = db['messages']
    collection.insert_one(user)
    return ConversationHandler.END
    
start_handler = CommandHandler('start', start)

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
    entry_points=[start_handler],
    states={
        STUDENTQN: [MessageHandler(Filters.text, handle_studentqn)],
        GENDERQN: [MessageHandler(Filters.text, handle_genderqn)],
        NAMEQN: [MessageHandler(Filters.text, handle_nameqn)],\
        HAPPINESSQN: [MessageHandler(Filters.text, handle_happinessqn)]
    },
    fallbacks=[],
)

# Create the Telegram bot instance
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Add the handlers to the dispatcher
# dispatcher.add_handler(start_handler)
# dispatcher.add_handler(store_data_handler)
# dispatcher.add_handler(retrieve_data_handler)
dispatcher.add_handler(conversation_handler)
# Start the bot
updater.start_polling()
