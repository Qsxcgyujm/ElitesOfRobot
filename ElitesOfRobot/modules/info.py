import html
import re
import os
import requests

from telethon import events 

from telegram import Update, ParseMode
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from ElitesOfRobot import (DEV_USERS, OWNER_ID, SUDO_USERS, SUPPORT_USERS,
                           WHITELIST_USERS, dispatcher, client)
from ElitesOfRobot.__main__ import USER_INFO, TOKEN
from ElitesOfRobot.modules.disable import DisableAbleCommandHandler
from ElitesOfRobot.modules.sql.antispam_sql import is_user_gbanned
from ElitesOfRobot.modules.sql.redis import is_user_afk, afk_reason
from ElitesOfRobot.modules.sql.users_sql import get_user_num_chats
from ElitesOfRobot.modules.sql.feds_sql import get_user_fbanlist 
from ElitesOfRobot.modules.helper_funcs.extraction import extract_user, get_user
import ElitesOfRobot.modules.sql.userinfo_sql as sql



OFFICERS = [OWNER_ID] + DEV_USERS + SUDO_USERS 


#HELTH-BAR - Show User Health -- This Feature From @SaitamaRobot
def no_by_per(totalhp, percentage):
    """
    rtype: num of `percentage` from total
    eg: 1000, 10 -> 10% of 1000 (100)
    """
    return totalhp * percentage / 100


def get_percentage(totalhp, earnedhp):
    """
    rtype: percentage of `totalhp` num
    eg: (1000, 100) will return 10%
    """

    matched_less = totalhp - earnedhp
    per_of_totalhp = 100 - matched_less * 100.0 / totalhp
    per_of_totalhp = str(int(per_of_totalhp))
    return per_of_totalhp


def hpmanager(user):
    total_hp = (get_user_num_chats(user.id) + 10) * 10

    if not is_user_gbanned(user.id):

        # Assign new var `new_hp` since we need `total_hp` in
        # end to calculate percentage.
        new_hp = total_hp

        # if no username decrease 25% of hp.
        if not user.username:
            new_hp -= no_by_per(total_hp, 25)
        try:
            dispatcher.bot.get_user_profile_photos(user.id).photos[0][-1]
        except IndexError:
            # no profile photo ==> -25% of hp
            new_hp -= no_by_per(total_hp, 25)
        # if no /setme exist ==> -20% of hp
        if not sql.get_user_me_info(user.id):
            new_hp -= no_by_per(total_hp, 20)
        # if no bio exsit ==> -10% of hp
        if not sql.get_user_bio(user.id):
            new_hp -= no_by_per(total_hp, 10)

        if is_user_afk(user.id):
            afkst = afk_reason(user.id)
            # if user is afk and no reason then decrease 7%
            # else if reason exist decrease 5%
            if not afkst:
                new_hp -= no_by_per(total_hp, 7)
            else:
                new_hp -= no_by_per(total_hp, 5)

        # fbanned users will have (2*number of fbans) less from max HP
        # Example: if HP is 100 but user has 5 diff fbans
        # Available HP is (2*5) = 10% less than Max HP
        # So.. 10% of 100HP = 90HP

        _, fbanlist = get_user_fbanlist(user.id)
        new_hp -= no_by_per(total_hp, 2 * len(fbanlist))

    # Bad status effects:
    # gbanned users will always have 5% HP from max HP
    # Example: If HP is 100 but gbanned
    # Available HP is 5% of 100 = 5HP

    else:
        new_hp = no_by_per(total_hp, 5)

    return {
        "earnedhp": int(new_hp),
        "totalhp": int(total_hp),
        "percentage": get_percentage(total_hp, new_hp)
    }


def make_bar(per):
    done = min(round(per / 10), 10)
    return "█" * done + "▓" * (10 - done)






#information
@run_async
def info(update: Update, context: CallbackContext):
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
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    
    text = (f"<b>• User Information :-</b>\n\n"
            f"∘ ID: <code>{user.id}</code>\n"
            f"∘ First Name: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\n∘ Last Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\n∘ Username: @{html.escape(user.username)}"

    
    isafk = is_user_afk(user.id)
    try:
        text += "\n\n∘ Currently AFK: "
        if user.id == bot.id:
             text += "<code>???</code>"
        else:
             text += str(isafk)
    except:
         pass

    try:
        if user.id == bot.id:
           num_chats = "???"
        else:
           num_chats = get_user_num_chats(user.id)
       
        text += f"\n∘ Mutual Chats: <code>{num_chats}</code> "
    except BadRequest:
        pass
    



    
    try:
        status = status = bot.get_chat_member(chat.id, user.id).status
        if status:
               if status in "left":
                   text += "\n∘ Chat Status: <em>Not Here!</em>"
               elif status == "member":
                   text += "\n∘ Chat Status: <em>Is Here!</em>"
               elif status in "administrator":
                   text += "\n∘ Chat Status: <em>Admin!</em>"
               elif status in "creator": 
                   text += "\n∘ Chat Status: <em>Creator!</em>"
    except BadRequest:
        pass
    
    
    
    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}")
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\n∘ Admin Title: <code>{custom_title}</code> \n"
    except BadRequest:
        pass

    if user_id not in [bot.id, 777000, 1087968824]:
        userhp = hpmanager(user)
        text += f"\n∘ Health : <code>{userhp['earnedhp']}/{userhp['totalhp']}</code> ∙ <code>{userhp['percentage']}% </code> \n( {make_bar(int(userhp['percentage']))} ) \n "                                                                                         

   
    if user.id == OWNER_ID:
        text += "\n<b>This Person Is My Master!</b>"

    elif user.id in DEV_USERS:
        text += "\n∘ <b>DEV USER: </b><i>Yes!</i>  "
        
    elif user.id in SUDO_USERS:
        text += "\n∘ <b>SUDO USER: </b><i>Yes!</i>  " 
        
    elif user.id in SUPPORT_USERS:
        text += "\n∘ <b>SUPPORT USER: </b><i>Yes!</i> "
       
    elif user.id in WHITELIST_USERS:
        text += "\n∘ <b>WHITELIST USER: </b><i>Yes!</i> "
       
    elif user.id == bot.id:
        text+= "\n\nI've Seen Them In... Wow. Are They Stalking Me? They're In All The Same Places I Am... Oh. It's Me.\n"


    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue

        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += "\n" + mod_info
    
    message.reply_text(
            text, parse_mode=ParseMode.HTML)

    


@client.on(events.NewMessage(pattern="^[!/]id(?: |$)(.*)"))
async def useridgetter(target):
    replied_user = await get_user(target)
    user_id = target.from_id
    user_id = replied_user.user.id
    first_name = replied_user.user.first_name
    username = replied_user.user.username

    first_name = first_name.replace("\u2060", "") if first_name else ("☠️ Deleted Account") 
    username = "@{}".format(username) if username else ("{}".format(first_name))

    await target.reply("**Name:** {} \n**User ID:** `{}`\n**Chat ID: `{}`**".format(
        username, user_id, str(target.chat_id)))



INFO_HANDLER = DisableAbleCommandHandler("info", info)

dispatcher.add_handler(INFO_HANDLER)
