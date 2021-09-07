from pyrogram import Client, MessageHandler
from pyrogram.api import types, functions
from threading import Timer
import time
from datetime import datetime, timedelta
import os

CODE = None


def get_code():
    while "tm_reg_code.txt" not in os.listdir():
        time.sleep(1)
    with open("tm_reg_code.txt", 'r') as file:
        global CODE
        CODE = file.read()  # Get your code programmatically


def phone_code_callback():
    t = Timer(2, get_code)
    t.start()
    while "tm_reg_code.txt" not in os.listdir():
        time.sleep(1)
    time.sleep(2)
    global CODE
    return CODE


def get_client(user):
    session = user.tm_sesison
    client = Client(session)
    client.start()
    return client


def auth(phone):
    client = Client(
        session_name='tm_sessions/' + phone,
        phone_number=phone,
        phone_code=phone_code_callback,
    )
    client.start()
    client.add_handler(MessageHandler(update_handler))


def send_message(client, target, text):
    client.send_message(target, text)


def forward_messages(client, target, from_id, message_ids):
    client.forward_messages(target, from_id, message_ids)


# target - id второго участника переписки, имеет тип str / int, number - номер для удобства хранения переписок
# def get_messages(session, target, offset=0, limit=50):
#     client = Client(session_name=session)
#     client.start()
#     messages_info = client.send(
#         functions.messages.GetHistory(
#             client.resolve_peer(target),
#             0, 0, offset, limit, 0, 0, 0
#         )
#     )
#     user = json.loads(str(client.get_me()))['user']
#     messages_info = json.loads(str(messages_info))
#     client.stop()
#     return message_parsing(messages_info, user)


def get_messages(client, target, offset=0, limit=50):
    messages_info = client.send(
        functions.messages.GetHistory(
            client.resolve_peer(target),
            0, 0, offset, limit, 0, 0, 0
        )
    )
    # with open('tm_raw_messages.txt', 'w') as file:
    #     file.write(str(messages_info))
    return dict(chat_photo=None, messages=message_parsing(messages_info, client.get_me()))


def message_parsing(messages_info, me):
    users = {user.id: user.first_name + (' ' + user.last_name if user.last_name is not None else '')
             for user in messages_info.users}
    user_id = me.id
    parsed_dict = [dict(
        name=users[message.from_id],
        text=message.message + ('\n' + message.media.webpage.url) if message.media and
                                                                     type(message.media) is types.MessageMediaWebPage
        and type(message.media.webpage) is not types.WebPageEmpty else '',
        date=datetime.fromtimestamp(message.date) + timedelta(hours=3),
        side='right' if user_id == message.from_id else 'left',
    ) for message in messages_info.messages]
    return parsed_dict


def get_user(client, target, destination):
    if not client.is_started:
        client.start()
    if type(destination) is types.PeerUser:
        user = client.resolve_peer(target)
        user = client.send(
            functions.users.GetFullUser(user)
        )

        username = user.user.first_name + ' ' + (user.user.last_name if user.user.last_name is not None else '')
        return username
    elif type(destination) is types.PeerChat or type(destination) is types.PeerChannel:
        chat_id = destination.chat_id
        chat = client.get_chat(chat_id)
        return chat.title


def get_dialogs(client):
    dialogs = client.send(
        functions.messages.GetDialogs(0, 0, types.InputPeerEmpty(), 1000)
    )
    res = parse_dialogs(dialogs, client.get_me())
    return res


def parse_dialogs(dialogs, me):
    messages = dialogs.messages
    users = {user.id: user for user in dialogs.users}
    chats = {chat.id: chat for chat in dialogs.chats}
    get_user_finctions = {types.PeerUser: lambda peer: users[peer.user_id].first_name + (' ' +
                                                                                         users[peer.user_id].last_name
                                                                                         if users[
                                                                                                peer.user_id].last_name is not None else ''),
                          types.PeerChat: lambda peer: chats[peer.chat_id].title,
                          types.PeerChannel: lambda peer: chats[peer.channel_id].title}
    dialogs = []
    for message in messages:
        if 'message' in message.__dict__:
            res = dict(date=datetime.fromtimestamp(message.date) + timedelta(hours=3),
                       last_message=message.message,
                       fwd_from=message.fwd_from,
                       photo='https://goo.gl/s6ce2P')

            if type(message.to_id) is types.PeerUser:
                if message.to_id.user_id != me.id:
                    res['id'] = message.to_id.user_id
                    res['name'] = get_user_finctions[type(message.to_id)](message.to_id)
                else:
                    res['id'] = message.from_id
                    res['name'] = users[message.from_id].first_name + (' ' + users[message.from_id].last_name if users[message.from_id].last_name is not None else '')
                res['is_chat'] = False
            else:
                res['id'] = message.to_id.__dict__[list(message.to_id.__dict__.keys())[-1]]
                res['name'] = get_user_finctions[type(message.to_id)](message.to_id)
                res['is_chat'] = True
            dialogs.append(res)
    return dialogs


def update_handler(_, update):
    message = dict(
        id=update.message_id,
        date=datetime.fromtimestamp(update.date) + timedelta(hours=3),
        text=update.text,
        chat_id=update.chat.id
    )


def send_photo(client, target, photo):
    client.send_photo(target, photo)


def send_audio(client, target, audio):
    client.send_audio(target, audio)


def send_document(client, target, document):
    client.send_document(target, document)


def send_video(client, target, video):
    client.send_video(target, video)


def send_voice(client, target, voice):
    client.send_voice(target, voice)
