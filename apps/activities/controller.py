import datetime
from enum import Enum

from sqlalchemy import and_
from sqlalchemy import distinct
from sqlalchemy import func

from apps.activities.models import Activity, ActivityEvent
from apps.main.models import User
from core.controllers import AppController
from core.db import DbSession

__author__ = 'Xomak'


class ActivitiesAppController(AppController):
    class ActionType(Enum):
        TO_DO = "сделать"
        DONE = "сделано"
        MOVE = "перенос"
        ABSENT = "невозможно"

    _is_in_chat = False
    _initialized = False

    def _initialize(self, message):
        if message.chat.id < 0:
            self._is_in_chat = True
            self._bot.send_message(message.chat.id, "Здорова, парни!")
        self._initialized = True

    def _create_task(self, user_id, activity_id, db_session, moved_task):
        new_task = ActivityEvent()
        new_task.user_id = user_id
        new_task.activity_id = activity_id
        new_task.status = 'pending'
        if moved_task:
            new_task.assign_type = 'move'
        db_session.add(new_task)
        db_session.commit()

    def _get_current_turn(self, activity_id, db_session):
        oldest_activity = db_session.query(func.max(ActivityEvent.datetime), ActivityEvent.user_id, ActivityEvent.id) \
            .filter(
            and_(
                ActivityEvent.status.in_(['moved', 'absent', 'done', 'compensated']),
                ActivityEvent.activity_id == activity_id,
                ActivityEvent.assign_type == 'queue'
            )) \
            .group_by(ActivityEvent.user_id) \
            .order_by(ActivityEvent.datetime) \
            .first()
        return oldest_activity[1] if oldest_activity is not None else None

    def _assign_to_activity(self, activity, db_session):
        moved_activities = db_session.query(ActivityEvent).filter_by(status='moved', activity_id=activity.id) \
            .order_by('datetime').all()
        last_activity = db_session.query(ActivityEvent).filter_by(activity_id=activity.id) \
            .order_by(ActivityEvent.datetime.desc()).first()
        current_turn_user_id = self._get_current_turn(activity.id, db_session)
        print("CU:" + str(current_turn_user_id))
        performed_users = db_session.query(distinct(ActivityEvent.user_id)) \
            .filter(ActivityEvent.activity_id == activity.id) \
            .all()
        performed_users_ids = [user[0] for user in performed_users]
        all_users = db_session.query(User).all()

        names = dict()
        for user in all_users:
            names[user.id] = user.name

        if len(performed_users_ids) != all_users:
            for user in all_users:
                if user.id not in performed_users_ids:
                    current_turn_user_id = user.id
                    break

        for moved_activity in moved_activities:
            if moved_activity.user_id == current_turn_user_id:
                self._create_task(moved_activity.user_id, activity.id, db_session, False)
                msg = "{username}, ты не выполнил свою обязанность {datetime} и очередь снова дошла до тебя." \
                    .format(username=moved_activity.user.name, datetime=moved_activity.datetime)
                return msg
            else:
                if moved_activity.user_id != last_activity.user_id:
                    self._create_task(moved_activity.user_id, activity.id, db_session, True)
                    msg = "{username}, ты не выполнил свою обязанность {datetime}, так что твоя очередь." \
                        .format(username=moved_activity.user.name, datetime=moved_activity.datetime)
                    return msg

        self._create_task(current_turn_user_id, activity.id, db_session, False)
        msg = "{username}, твоя очередь." \
            .format(username=names[current_turn_user_id])
        return msg

    def _mark_activity_as_moved(self, activity_event, db_session):
        if activity_event.assign_type == 'queue':
            activity_event.status = 'moved'
            msg = "Увеличиваю твой долг на единицу."
        else:
            activity_event.status = 'moved_gracefully'
            msg = "Окей, попросим в следующий раз."
        db_session.commit()
        return msg

    def _mark_activity_as_absent(self, activity_event, db_session):
        activity_event.status = 'absent'
        msg = "Я поняла."
        db_session.commit()
        return msg

    def _mark_activity_as_done(self, activity_event, db_session):
        if activity_event.assign_type == 'move':
            moved_to_close = db_session.query(ActivityEvent).filter_by(activity_id=activity_event.activity_id,
                                                                       user_id=activity_event.user_id,
                                                                       status='moved').first()
            if moved_to_close is not None:
                moved_to_close.status = 'compensated'
                moved_to_close.compensated_by_id = activity_event.id

        activity_event.complete_datetime = datetime.datetime.now()
        activity_event.status = 'done'
        db_session.commit()

    def handle_in_chat(self, message):

        session = DbSession()
        two_parts = message.text.split(' ')
        current_user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

        if len(two_parts) == 2 is not None and two_parts[0].startswith('#'):
            command_string = two_parts[0][1:]
            action = None
            try:
                action = self.ActionType(two_parts[1])
            except Exception:
                self._bot.send_message(message.chat.id, "Ты о чём, алё?")

            if action is not None:
                command = session.query(Activity).filter_by(do_command=command_string).first()

                if command is not None:

                    pending_activity = session.query(ActivityEvent).filter_by(status='pending',
                                                                              activity_id=command.id).first()
                    if action == self.ActionType.TO_DO:
                        if pending_activity is None:
                            self._bot.send_message(message.chat.id, "Ща кого-то припахаем.")
                            msg = self._assign_to_activity(command, session)
                            self._bot.send_message(message.chat.id, msg)
                        else:
                            self._bot.send_message(message.chat.id, "Мы уже ждём, пока {username} с этим разберется."
                                                   .format(username=pending_activity.user.name))
                    elif action == self.ActionType.DONE:
                        if pending_activity.user_id != current_user.id:
                            self._mark_activity_as_done(pending_activity, session)
                            self._bot.send_message(message.chat.id, "Спасибо. Дело закрыто.")
                        else:
                            self._bot.send_message(message.chat.id, "Ты не можешь подтвердить выполнение действия. "
                                                                    "Попроси кого-то другого.")
                    elif action == self.ActionType.MOVE:
                        msg = self._mark_activity_as_moved(pending_activity, session)
                        self._bot.send_message(message.chat.id, msg)
                        msg = self._assign_to_activity(command, session)
                        self._bot.send_message(message.chat.id, msg)
                    elif action == self.ActionType.ABSENT:
                        msg = self._mark_activity_as_absent(pending_activity, session)
                        self._bot.send_message(message.chat.id, msg)
                        msg = self._assign_to_activity(command, session)
                        self._bot.send_message(message.chat.id, msg)

                else:
                    self._bot.send_message(message.chat.id, "Ты о чём, алё?")
        session.close()

    def handle_message(self, message, session):
        if not self._initialized:
            self._initialize(message)
        if self._is_in_chat:
            self.handle_in_chat(message)
        else:
            self._bot.send_message(message.chat.id, "Я пока не умею общаться лично.")
