from apps.main.controller import MainAppController

__author__ = 'Xomak'

class Session:
    controller = None
    data = None

    def handle_message(self, message):
        self.controller.handle_message(message, self)


class SessionsController:

    _bot = None
    sessions = dict()

    def __init__(self, bot):
        self._bot = bot

    def get_default_controller(self):
        return MainAppController(self._bot)

    def get_session_by_chat_id(self, chat_id):
        if chat_id not in self.sessions:
            session = Session()
            session.controller = self.get_default_controller()
            self.sessions[chat_id] = session
        return self.sessions[chat_id]

