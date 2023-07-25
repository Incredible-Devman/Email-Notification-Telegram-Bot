import imaplib
import time
import os, signal
import threading
import logging

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode, ReplyKeyboardMarkup, KeyboardButton


EMAIL_NAME = os.environ.get('EMAIL_NAME')
EMAIL_PW = os.environ.get('EMAIL_PW')

TG_TOKEN = os.environ.get('TG_CHECKMYMAILBOT_TOKEN')


chats=[] # for storing all active chat_id's

updater = Updater(
    token=TG_TOKEN,
    use_context=True
)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Reply Keyboard for start and stop buttons
keyboard = [[KeyboardButton(text = "/start"), KeyboardButton(text = "/stop")]]
options = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def run_checking(cur_chat_id):

    """
    Check a number of incoming emails for every 10 seconds
    and notifies user about new messages if that number changed from last time

    Parameters
    ----------
    cur_chat_id : 
    """

    last_number_msg = 0     # How many emails we got after last check
    cur_number_msg = 0      # How many emails we got now

    # Initiate connection to a mail server
    with imaplib.IMAP4_SSL(
                # host='imap.yandex.ru',
                host='outlook.live.com',
                port=993
        ) as M:

        M.login(EMAIL_NAME, EMAIL_PW) # Authentification
        print("chat num: ", len(chats))
        while True:

            # If we don't have any active chats, then break out of a function 
            if str(cur_chat_id) not in chats:
                return

            # Get a current number of incoming messages
            cur_number_msg = int(*M.select(mailbox='INBOX', readonly=True)[1])

            # Works only one time, after start.
            # We get and show number of unseen messages.
            if not(last_number_msg):

                (_, messages) = M.search(None, '(UNSEEN)')
                unseen_number = len(messages[0].decode('utf-8').split())

                dispatcher.bot.send_message(
                    chat_id=cur_chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'✉️ Now you have <b>{unseen_number}</b> unseen messages.'
                )

                last_number_msg = cur_number_msg

            # If the number of incoming messages changed, 
            # then send a notification (message)
            if cur_number_msg > last_number_msg:

                dispatcher.bot.send_message(
                    chat_id=cur_chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'📩 New message!'
                )

                last_number_msg = cur_number_msg

            # We check mail every 10 seconds
            time.sleep(10)


def start(update, context):

    """
    Basic command. Works one time, after getting /start from user.

    Parameters
    ----------
    update : 
    context : 
    """

    # Chat id
    cur_chat_id = update.message.chat_id

    # We start a new thread only if its id is not in active chats list
    if cur_chat_id not in chats:

        # Add chat_id to active chats list
        save_chat(str(cur_chat_id))

        # Welcome message
        dispatcher.bot.send_message(
            chat_id=cur_chat_id,
            parse_mode=ParseMode.HTML,
            text="Hi! I'm Alex, your new email assistant. I'll notify you every time you get a new email.\n\n\
<b>Be careful:</b> I'm falling asleep at 12am and waking up at 6am every day 😴 🛌",
            reply_markup=options
        )

        # Create new thread
        run_thread_for_chat(cur_chat_id)


    else:
        # Else we send a warning message
        context.bot.send_message(
            chat_id=cur_chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, don\'t mess with me, okay? I\'m already running.',
        )


def stop(update, context):
    
    """
    Stops thread and getting updates from a mail server.

    Parameters
    ----------
    update : 
    context : 
    """

    # It shouldn't work before the bot is running
    if chats == []:

        context.bot.send_message(
            update.message.chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, you should run me first!',
        )
        return

    # Remove chat_id from active chats list
    chats.remove(str(update.message.chat_id))

    # And send a farewell message
    context.bot.send_message(
        update.message.chat_id,
        parse_mode=ParseMode.HTML,
        text=f'I was glad to help you. Bye 👋',
    )


def run_thread_for_chat(chat_id):
    new_thread = threading.Thread(target=run_checking, args=(chat_id, ))
    new_thread.start()


def save_chat(chat_id):

    if chat_id not in chats:
        
        # write to global variable
        chats.append(chat_id)
        
        # write to storage
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, 'active_chats.storage')

        with open(file_path, 'a') as active_chats:
            active_chats.write(chat_id)
            active_chats.write('\n')


def remove_chat():
    pass


def main():

    startHandler = CommandHandler('start', start)
    stopHandler = CommandHandler('stop', stop)

    dispatcher.add_handler(startHandler)
    dispatcher.add_handler(stopHandler)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'active_chats.storage')

    updater.start_polling()    

    with open(file_path, 'r') as active_chats:
        lines = active_chats.readlines()

        if lines != []:
            for line in lines:
                chats.append(line.strip())
        print("chats : ", len(chats))
        if chats != []:
            for chat_id in chats:
                run_thread_for_chat(chat_id)

    updater.idle()


if __name__ == '__main__':
    main()