from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from ElitesOfRobot.__main__ import STATS, USER_BOOK
from ElitesOfRobot import dispatcher, spamwtc 

from ElitesOfRobot.modules.disable import DisableAbleCommandHandler
from ElitesOfRobot.modules.sql.users_sql import get_user_num_chats
from ElitesOfRobot.modules.helper_funcs.extraction import extract_user   
                                                                                                                                              
import ElitesOfRobot.modules.helper_funcs.cas_api as cas
import ElitesOfRobot.modules.sql.userinfo_sql as sql



@run_async
def book(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@") and
         not args[0].isdigit() and
         not message.parse_entities([MessageEntity.TEXT_MENTION]))):
        message.reply_text("I Can't Extract A User From This.")
        return

    else:
        return

    
    text = (f"<b>User Status :</b>"
            f"<code> {user.id} </code>")
    
    
    if chat.type != "private" and user_id != bot.id:
        _stext = "\n\n<b>• Current Chat Status : </b>{}"
        status = status = bot.get_chat_member(chat.id, user.id).status
        if status:
           if status in "kicked":
              text += _stext.format("Banned!")
           elif status == "restricted":
              text += _stext.format("Muted!")


       
    text += "\n\n<b>• Other Status</b>"
    text += "\n<b>CAS Banned : </b>"
    result = cas.banchecker(user.id)
    text += str(result)

    try:
        spamwtc = spamwtc.get_ban(int(user.id))
        if spamwtc:
            text += "\n<b>Spamwatch Banned :</b> True"
            text += f"\n<b>Reason :</b> <pre>{spamwtc.reason}</pre>"
        else:
            text += "\n<b>Spamwatch Banned :</b> False"
    except:
        pass  # don't crash if api is down somehow...


    text += f"\n\n<b>• {dispatcher.bot.first_name} Status</b>"
    for mod in USER_BOOK:
        if mod.__mod_name__ == "Users":
            continue

        try:
            mod_book = mod.__user_book__(user.id)
        except TypeError:
            mod_book = mod.__user_book__(user.id, chat.id)
        if mod_book:
            text += "\n" + mod_book
                    
    


    message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    
BOOK_HANDLER = DisableAbleCommandHandler(("book"), book, pass_args=True)
dispatcher.add_handler(BOOK_HANDLER)

__handler__ = [BOOK_HANDLER]
