from apps.activities.controller import ActivitiesAppController
from apps.main.models import User
from core.controllers import AppController
from core.db import DbSession

__author__ = 'Xomak'


class MainAppController(AppController):

    def has_access(self, telegram_id):
        db_session = DbSession()
        users_count = db_session.query(User).filter_by(telegram_id=telegram_id).count()
        db_session.close()
        return users_count == 1

    def handle_message(self, message, session):
        telegram_id = message.from_user.id
        if self.has_access(telegram_id):
            session.controller = ActivitiesAppController(self._bot)
            session.handle_message(message)
        else:
            self._bot.send_message(message.chat.id, "Прости. Я не разговариваю с посторонними.")
