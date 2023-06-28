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

DELETEQN = range(1)

# Start command handler
def delete(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Deleting your account cannot be undone. Are you sure you want to delete your account?")
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='Yes')],
        [InlineKeyboardButton("No", callback_data='No')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Delete your account?', reply_markup=reply_markup)
    return DELETEQN

def handle_delete(update, context):
    query = update.callback_query
    chosen_option = query.data
    userid = update.effective_chat.id
    if chosen_option == 'Yes':
        userid = update.effective_user.id
        collection = db['messages']
        collection.delete_one({'userid': userid})
        context.bot.send_message(chat_id=userid, text="Sad to see you go! Use /setup to create your account again!")
        return ConversationHandler.END
    if chosen_option == "No":
        context.bot.send_message(chat_id=userid, text="Glad to see you're still here! Your account has not been deleted.")
        return ConversationHandler.END



# Create Conversation Handler
delete_handler = ConversationHandler(
    entry_points=[CommandHandler('delete', delete)],
    states={
        DELETEQN: [CallbackQueryHandler(handle_delete)],
    },
    fallbacks=[],
)
