from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import UserIsBlocked
import motor.motor_asyncio
import configparser
import sys
import os
from asyncio import sleep
from time import time
from collections import defaultdict
from typing import Union

config_path = os.path.join(sys.path[0], 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)
me_chat_id = config.get('anime_girl', 'chat_id')
MongoDB = config.get('anime_girl', 'db_url')
connectDB = motor.motor_asyncio.AsyncIOMotorClient(MongoDB)
createDB = connectDB.feedback_bot
USERS = defaultdict(list)
MESSAGES = 10
SECONDS = 5
MEDIA_GROUP = defaultdict(list)
MESSAGES_GROUP = 1
SECONDSGROUP = 5
users = createDB["users"]
blocklist = createDB["block_id"]
flood = createDB["flood"]
message_ids = createDB["message_ids"]
promoted_id = createDB["admins"]


async def admins_id(client: Client, message: Message):
    list_adm = [int(_["USER_ID"]) async for _ in promoted_id.find()]
    return list_adm


async def admin_is_true(client: Client, message: Message):
    list_admA = await admins_id(client, message)
    if message.from_user.username == me_chat_id:
        return True
    elif message.from_user.id in list_admA:
        return True
    else:
        return False


async def db_write(message: Message):
    user = await users.find_one({"USER_ID": f"{message.chat.id}"})
    if user:
        pass
    else:
        user = {"USER_ID": f"{message.chat.id}"}
        await users.insert_one(user)


async def db_chek_blocklist(message: Message):
    user = await blocklist.find_one({"USER_ID": f"{message.chat.id}"})
    if user:
        return False
    else:
        return True


async def send_all_message(client: Client, message: Message):
    count = 0
    async for _ in users.find():
        try:
            if message.message.reply_to_message:
                if message.message.reply_to_message.media_group_id:
                    await sleep(1.5)
                    await client.copy_media_group(_["USER_ID"],
                                                  me_chat_id,
                                                  message_id=message.message.reply_to_message.message_id)
                else:
                    await message.message.reply_to_message.forward(_["USER_ID"])
            else:
                await client.copy_message(_["USER_ID"],
                                          me_chat_id,
                                          message_id=message.message.message_id)
            count += 1
        except UserIsBlocked:
            await users.delete_one({"USER_ID": f"{_['USER_ID']}"})
        except:
            pass
    _url_ = await message.message.reply_text("<b>Сообщение успешно разослано {} пользователям</b>".format(count))
    await sleep(5)
    await _url_.delete()


async def isFlood(message: int) -> Union[bool, None]:
    USERS[message.from_user.id].append(time())
    if len(list(filter(lambda x: time() - int(x) < SECONDS, USERS[message.from_user.id]))) > MESSAGES:
        return False


async def media_group_id(message: Message) -> Union[bool, None]:
    MEDIA_GROUP[message.media_group_id].append(time())
    if len(list(filter(lambda x: time() - int(x) < SECONDSGROUP, MEDIA_GROUP[message.media_group_id]))) > MESSAGES_GROUP:
        return False


async def flood_control(message: Message):
    if await isFlood(message) is False:
        chek_antiflood = await flood.find_one({"ENABLE": "YES"})
        if chek_antiflood:
            user = await blocklist.find_one({"USER_ID": f"{message.from_user.id}"})
            if message.media_group_id:
                media_group = await media_group_id(message)
                if media_group != False:
                    if user \
                            and message.from_user.username != me_chat_id:
                        await message.reply_text("<b>Ты заблокирован в этом боте навсегда</b>",
                                                 reply_to_message_id=message.message_id)
                    elif user is None \
                            and message.from_user.username != me_chat_id:
                        user = {"USER_ID": f"{message.from_user.id}"}
                        await blocklist.insert_one(user)
                        await message.reply_text("<b>Ты заблокирован в этом боте навсегда</b>",
                                                 reply_to_message_id=message.message_id)
                        return False
            else:
                if user \
                        and message.from_user.username != me_chat_id:
                    await message.reply_text("<b>Ты заблокирован в этом боте навсегда</b>",
                                             reply_to_message_id=message.message_id)
                elif user is None \
                        and message.from_user.username != me_chat_id:
                    user = {"USER_ID": f"{message.from_user.id}"}
                    await blocklist.insert_one(user)
                    await message.reply_text("<b>Ты заблокирован в этом боте навсегда</b>",
                                             reply_to_message_id=message.message_id)
                    return False
        else:
            return True
