from pymongo import MongoClient
from telegram import Bot
from telegram.ext import CommandHandler, Updater

# MongoDB connection configuration
mongo_client = MongoClient('mongodb+srv://tylerlian2021:CytaQbiGsjwFwe8k@bfgsafespace.tnob2zh.mongodb.net/')
db = mongo_client['your_database_name']  # Replace 'your_database_name' with your desired database name

# Telegram bot configuration
bot_token = '6274496403:AAGehEhKyVAGNOQ8c75y8Y5DE-Muu9x1w50'  # Replace 'your_bot_token' with the actual bot token
bot = Bot(token=bot_token)

# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hello! Welcome to the bot.')

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

# Create the Telegram bot instance
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Add the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(store_data_handler)
dispatcher.add_handler(retrieve_data_handler)

# Start the bot
updater.start_polling()
