import html
from telegram import Message, Update, User, Chat, ParseMode
from typing import List, Optional

from telegram import ChatPermissions
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

from ElitesOfRobot import dispatcher, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, ERROR_DUMP
from ElitesOfRobot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from ElitesOfRobot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from ElitesOfRobot.modules.helper_funcs.filters import CustomFilters 
from ElitesOfRobot.modules.sql.users_sql import get_all_chats
import ElitesOfRobot.modules.sql.global_kicks_sql as sql

GKICK_ERRORS = {
    "Bots can't add new chat members",
    "Channel_private",
    "Chat not found",
    "Can't demote chat creator",
    "Chat_admin_required",
    "Group chat was deactivated",
    "Method is available for supergroup and channel chats only",
    "Method is available only for supergroups",
    "Need to be inviter of a user to kick it from a basic group",
    "Not enough rights to restrict/unrestrict chat member",
    "Not in the chat",
    "Only the creator of a basic group can kick group administrators",
    "Peer_id_invalid",
    "User is an administrator of the chat",
    "User_not_participant",
    "Reply message not found",
    "User not found"
}



OFFICERS = [OWNER_ID] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS


@run_async
def gkick(update, context):
    message = update.effective_message
    args = context.args
    bot = context.bot
    user_id = extract_user(message, args)
    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in GKICK_ERRORS:
            pass
        else:
            message.reply_text("Unexpected Error!")
            context.bot.send_message(ERROR_DUMP, "User cannot be Globally kicked because: {}".format(excp.message))
            return
    except TelegramError:
            pass

    if not user_id or int(user_id)==777000:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if int(user_id) in OFFICERS:
        message.reply_text("Error! (^_-)")
        return 
        
    if user_id == context.bot.id: 
        message.reply_text("Error! (¯―¯٥)")
        return    

    chats = get_all_chats()
    banner = update.effective_user  # type: Optional[User]
    
    message.reply_text("Globally kicking user @{}".format(user_chat.username))
    sql.gkick_user(user_id, user_chat.username, 1)
    for chat in chats:
        try:
            member = context.bot.get_chat_member(chat.chat_id, user_id)
            if member.can_send_messages is False:
                context.bot.unban_chat_member(chat.chat_id, user_id)  # Unban_member = kick (and not ban)
                context.bot.restrict_chat_member(chat.chat_id, user_id, permissions=ChatPermissions(can_send_messages=False))
            else:
                context.bot.unban_chat_member(chat.chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GKICK_ERRORS:
                pass
            else:
                message.reply_text("Unexpected Error!")
                context.bot.send_message(ERROR_DUMP, "User cannot be Globally kicked because: {}".format(excp.message))
                return
        except TelegramError:
            pass

def __user_book__(user_id):
    times = sql.get_times(user_id)
    
    if int(user_id) in OFFICERS:
        text="<b>Globally Kicked : </b>❓ "
    else:
        text = "<b>Globally Kicked : </b>{}"
        if times!=0:
            text = text.format("Yes ( {} ) ".format(times))
        else:
            text = text.format("No")
    return text

@run_async
def gkickset(update, context):
    message = update.effective_message
    args = context.args 
    bot = context.bot
    user_id, value = extract_user_and_text(message, args)
    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in GKICK_ERRORS:
            pass
        else:
            message.reply_text("GENERIC ERROR: {}".format(excp.message))
    except TelegramError:
        pass
    if not user_id:
        message.reply_text("You do not seems to be referring to a user")
        return  

    if int(user_id) in OFFICERS:
        message.reply_text("Error! (^_-)")
        return

    if user_id == bot.id:
        message.reply_text("Error! (¯―¯٥)")
        return

    if not value:
        message.reply_text("Please Give Me A Valid Numerical Value (1 to 10) ")
        return
      
    sql.gkick_setvalue(user_id, user_chat.username, int(value))
    update.effective_message.reply_text("GKICK VALUE UPDATED!")
    return

def gkickreset(update, context):
    message = update.effective_message
    args = context.args
    bot = context.bot
    user_id, value = extract_user_and_text(message, args)
    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in GKICK_ERRORS:
            pass
        else:
            message.reply_text("GENERIC ERROR: {}".format(excp.message))
    except TelegramError:
        pass
    if not user_id:
        message.reply_text("You do not seems to be referring to a user")
        return  

    if int(user_id) in OFFICERS:
        message.reply_text("Error! (^_-)")
        return

    if user_id == bot.id:
        message.reply_text("Error! (¯―¯٥)")
        return
      
    sql.gkick_reset(user_id)
    update.effective_message.reply_text("GKICK RESETED!")
    return

			
GKICK_HANDLER = CommandHandler("gkick", gkick, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
SET_HANDLER = CommandHandler("gkickset", gkickset, pass_args=True,filters=Filters.user(OWNER_ID))
RESET_HANDLER = CommandHandler("gkickreset", gkickreset, pass_args=True,filters=Filters.user(OWNER_ID))

dispatcher.add_handler(GKICK_HANDLER)
dispatcher.add_handler(SET_HANDLER)
dispatcher.add_handler(RESET_HANDLER)
