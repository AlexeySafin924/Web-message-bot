import vk
from billy_the_messenger.settings import VK_APP_ID
from math import ceil
from datetime import datetime, timedelta
import time
from threading import Thread
user_sessions = {}


class VkUpdateHandler(Thread):
    def __init__(self, user):
        super().__init__()
        self.user = user

    def run(self):
        while True:
            print('I\'m handle your updates')
            if self.user in user_sessions:
                print('No error!!!')
                get_updates(self.user)
                time.sleep(1)
            else:
                print('Error!!!')
                self.user.has_vk = False
                self.user.save()
                break


def get_updates(user):
    api = get_api(user)
    updates = api.messages.getLongPollHistory(ts=user_sessions[user]['last_ts'],
                                              pts=user_sessions[user]['last_pts'],
                                              preview_length=0,
                                              onlines=True,
                                              lp_version=3,)
    user_sessions[user]['last_pts'] = updates['new_pts']
    messages = updates.get('messages')
    if messages['count']:
        new_messages = parse_update_message(messages['items'])
    else:
        return None
    # TODO: send updates to client
    # TODO: expand update variety
    return new_messages


def parse_update_message(message_info):
    if not message_info:
        return None
    messages = [dict(
        date=datetime.fromtimestamp(message['date']) + timedelta(hours=3),
        text=message['body'],
        attachments=parse_update_attachments(message.get('attachments')),
        chat_id=2000000000 + int(message['chat_id'])
        if message['title'] else message['user_id'],
        id=message['id'],
        fwd_messages=parse_update_message(message.get('fwd_messages')),
    ) for message in message_info]
    return messages


def set_update_handler(user):
    handler = VkUpdateHandler(user)
    print('handler was set')
    handler.start()


def parse_update_attachments(attachments):
    if not attachments:
        return None
    res = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            res.append(dict(type='photo', body=attachment['photo']['sizes'][-1]))


def get_api(user, login=None, password=None, update_lp_server=False):
    if user in user_sessions:
        session = user_sessions[user]['session']
    elif login is None or password is None:
        user.has_vk = False
        user.save()
        raise ValueError('login or password is none')
    else:
        session = vk.AuthSession(app_id=VK_APP_ID, user_login=login, user_password=password, scope=268435455)
    api = vk.API(session, v='5.74')
    if update_lp_server:
        lp_server = api.messages.getLongPollServer(need_pts=True, lp_version=3)
        user_sessions[user] = dict(session=session,
                                   last_ts=lp_server['ts'],
                                   last_pts=lp_server['pts'])
    # login = user.vk_login
    # password = user.vk_password
    # session = vk.AuthSession(app_id=VK_APP_ID, user_login=login, user_password=password, scope=268435455)
    # api = vk.API(session, v='5.74')
    return api


def get_friends():
    json_friends = get_api().friends.get(fields='nickname')
    friends = json_friends['items']
    count = json_friends['count']
    return count, friends


def send_message(api, id, message, fwd_messages):
    api.messages.send(user_id=id, message=message, forward_messages=fwd_messages)


def get_users(api, uids):
    users = api.users.get(user_ids=uids, fields=['photo_50', 'photo_max'])
    users = [dict(
        name=user.get('first_name', '') + ' ' + user.get('last_name', ''),
        photo_min=user['photo_50'],
        photo_max=user['photo_max'],
    ) for user in users]
    return users


def get_messages(api, target, offset, count, is_chat):
    target = int(target)
    message_info = api.messages.getHistory(offset=offset, count=count, peer_id=target + 2000000000 * is_chat)

    chat_photo, messages = message_parsing(api, target, is_chat, message_info['items'])

    return dict(chat_photo=chat_photo, messages=messages)


def message_parsing(api, target, is_chat, message_info, is_fwd=False):
    if not is_fwd:
        user_id = api.users.get()[0]['id']

        if is_chat:
            chat_info = api.messages.getChat(target)
            chat_users = chat_info['users']
            for item in chat_info[::-1]:
                if item.startswith('photo'):
                    chat_photo = chat_info['item']['photo_max']
                    break
        else:
            chat_users = [target, user_id]
            chat_photo = get_users(api, target)[0]['photo_max']
    else:
        chat_users = [message['user_id'] for message in message_info]
        chat_photo = None
    users_info = get_users(api, chat_users)
    users_info = dict(zip(chat_users, users_info))

    messages = []
    for message in message_info:
        res = dict(
            name=users_info[message['from_id']]['name'] if not is_fwd else users_info[message['user_id']]['name'],
            photo=users_info[message['user_id']]['photo_max'],
            date=datetime.fromtimestamp(message['date']) + timedelta(hours=3),
            text=message['body'],
            attachments=parse_attachments(message.get('attachments')),
        )
        if not is_fwd:
            res['message_id'] = message['id']
            res['side'] = 'right' if user_id == message['from_id'] else 'left'
        if 'fwd_messages' in message:
            res['fwd_messages'] = message_parsing(api, None, False, message['fwd_messages'], True)[-1]

        messages.append(res)

    return chat_photo, messages


def parse_attachments(attachments):
    if attachments is None:
        return None
    res = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            print(attachment['photo'])
            for item in list(attachment['photo'].keys())[::-1]:
                if item.startswith('photo'):
                    res.append(dict(type='photo', body=attachment['photo'][item]))
                    break
        else:
            res.append(dict(type='unknown'))
    return res


def get_dialogs(api):
    dialog_info = api.messages.getDialogs(count=200)
    # TODO: use execute instead of messages.getDialogs
    # code = '''
    # var dialogs_info = [];
    # var dialogs_amount = API.messages.getDialogs({'count': 0)['count'];
    # dialogs_info = [];
    # while (dalogs_amount) {
    #     dialogs_info.concat(API.messages.getDialogs({'count': 200, 'offset': dialogs_info.length});
    # }
    # return dialogs_info;
    # '''
    # dialogs_info = api.execute(code)
    if dialog_info['count'] > 200:
        for i in range(ceil(dialog_info['count'] / 200)):
            dialog_info['items'] += api.messages.getDialogs(offset=(i + 1) * 200, count=200)['items']
            time.sleep(0.34)

    dialogs = dialog_parsing(api, dialog_info)

    return dialogs


def dialog_parsing(api, dialog_info):
    # TODO: add bots in chats (their ids < 0)
    users = [dict(name=item['message']['title'],
                  photo=item['message'].get('photo_100', 'https://goo.gl/s6ce2P'), )  # kitten if no photo
             if item['message']['title'] else
             dict(name=item['message']['user_id'],
                  photo=None)
             for item in dialog_info['items'] if item['message']['user_id'] > 0]
    users_info = get_users(api, [user['name'] for user in users if type(user['name']) is int])

    counter = 0
    for i in range(len(users)):
        if type(users[i]['name']) is int:
            users[i]['name'] = users_info[counter]['name']
            users[i]['photo'] = users_info[counter]['photo_min']
            counter += 1

    dialog_info['items'] = [item for item in dialog_info['items'] if item['message']['user_id'] > 0]
    dialogs = [dict(
        name=users[i]['name'] if i < len(users) else 'Аркадий',
        photo=users[i]['photo'] if i < len(users) else '../../static/images/avatars/default.png',
        id=2000000000 + int(item['message']['chat_id']) if item['message']['title'] else item['message']['user_id'],
        date=datetime.fromtimestamp(item['message']['date']) + timedelta(hours=3),
        last_message=item['message']['body'],
        is_chat=bool(item['message']['title']),
    ) for i, item in enumerate(dialog_info['items'])]

    return dialogs
