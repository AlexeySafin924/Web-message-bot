from channels.generic.websocket import WebsocketConsumer
import json


class ChatConsumer(WebsocketConsumer):
    """Serves websockets for online\offline status update
    """

    def connect(self):
        """ Client's current mode. Either 'vk' or 'tm' """
        self.mode = self.scope['url_route']['kwargs']['mode']
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.accept()
        # Todo: get user from http(s) session

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        """ Get information about the dialog """
        id = text_data_json['id']
        # TODO: status updateg
        import time
        last_activity = int(time.time()) - 3600
        # last_activity =  getStatus(id)
        self.update(id, last_activity)

    def update(self, id, last_activity):
        self.send(text_data=json.dumps({
            'id': id,
            'lastActivity': last_activity
        }))
