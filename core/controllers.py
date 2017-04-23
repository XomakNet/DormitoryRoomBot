__author__ = 'Xomak'


class AppController:

    _bot = None

    def __init__(self, bot):
        self._bot = bot

    def handle_message(self, message, session):
        pass
