from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os
load_dotenv()
mongo_url = os.environ.get('MONGODB_URL')
mongo_client = MongoClient(mongo_url)
db = mongo_client['SafeSpaceDB'] 
userCollection = db['messages'] 
reportCollection = db['reports']
report = {
    "reporter": None,
    "reportee": None,
    "reason": None,
    "description": None,
    "datetime": None,
}

# Define conversation states
REPORT_REASON, REPORT_EVIDENCE = range(2)

def start_report(update, context):
    # Display reason selection keyboard
    keyboard = [
        [InlineKeyboardButton("Spam", callback_data='spam')],
        [InlineKeyboardButton("Harassment", callback_data='harassment')],
        [InlineKeyboardButton("Inappropriate content", callback_data='inappropriate')],
        [InlineKeyboardButton("Other", callback_data='other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="We are sorry to hear that you are affected by this. At any time you wish to cancel your report use /cancelreport")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Please select a reason for reporting the user:", reply_markup=reply_markup)

    return REPORT_REASON

def handle_reason_selection(update, context):
    query = update.callback_query
    report['reason'] = query.data

    # Request evidence from the reporter
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please copy paste the text as evidence to support your report.")
    
    return REPORT_EVIDENCE

def handle_evidence(update, context):
    evidence = update.message.text
    report["description"] = evidence
    # Save the report details in the database (you need to implement the database functionality)

    # Notify the reporter that the report has been successfully submitted
    update.message.reply_text("Thank you for your report. It has been successfully submitted.")
    report['reporter'] = update.effective_user.id
    user = userCollection.find_one({'userid': update.effective_user.id})
    partnerid = user['partnerid']
    report['reportee'] = partnerid
    userCollection.update_one(
        {'userid': update.effective_user.id},         {
            '$set': {'partnerid': None},
            '$push': {'reportedUsers': partnerid}
        }, upsert=True)
    userCollection.update_one({'userid': partnerid}, {'$set': {'partnerid': None}})
    context.bot.send_message(chat_id=update.effective_chat.id, text="Conversation cancelled. Please use /begin for a new partner!")
    context.bot.send_message(chat_id=partnerid, text="Conversation cancelled. Please use /begin for a new partner!")
    report['datetime'] = datetime.now()
    reportCollection.insert_one(report)
    return ConversationHandler.END

def cancel_report(update, context):
    # Handle the cancelation of the report process
    update.message.reply_text("Report canceled.")
    
    return ConversationHandler.END

# Create a conversation handler for reporting
report_handler = ConversationHandler(
    entry_points=[CommandHandler('report', start_report)],
    states={
        REPORT_REASON: [CallbackQueryHandler(handle_reason_selection)],
        REPORT_EVIDENCE: [MessageHandler(Filters.text, handle_evidence)]
    },
    fallbacks=[CommandHandler('cancelreport', cancel_report)]
)


