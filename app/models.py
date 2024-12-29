from app import app, db

import uuid
import random
import datetime

from pprint import pprint


class User(db.Model):

    SPECTATOR = 0
    EDITOR = 1
    BANNED = 2

    __tablename__ = 'users'
    id = db.Column(db.LargeBinary, primary_key=True, default=uuid.uuid4().bytes)
    fingerprint = db.Column(db.Text)
    public_id = db.Column(db.Text, unique=True, default=hex(random.randint(16 ** 3, 16 ** 11)).lstrip('0x'))
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    symbols = db.Column(db.Integer, default=app.config.get('DEFAULT_SYMBOLS_COUNT'))
    last_symbols_update = db.Column(db.DateTime, default=datetime.datetime.now())
    status = db.Column(db.Integer, default=SPECTATOR)

    def __repr__(self):
        return f'<User:{self.public_id}>'
    
    def is_banned(self):
        return self.status == User.BANNED
    
    def is_editor(self):
        return self.status == User.EDITOR
    
    def is_spectator(self):
        return self.status == User.SPECTATOR
    
    def ban(self):
        self.status = User.BANNED
    
    def unban(self):
        self.status = User.SPECTATOR
    
    def make_editor(self):
        self.status = User.EDITOR
    
    def make_spectator(self):
        self.status = User.SPECTATOR
    
    @staticmethod
    def get_by_raw_id(id):
        """Получение пользователя по байтовому id в hex формате, который лежит в cookie"""

        if id is None:
            return None
        
        try:
            id = int(id, 16).to_bytes(16, 'big')
        except OverflowError:
            return None
        user = User.query.filter(User.id == id).first()

        return user
    

class Action(db.Model):

    ADD = 0
    DELETE = 1
    REPLACE = 2
    BANNED = 3
    UNBANNED = 4
    TO_EDITOR = 5
    TO_SPECTATOR = 6

    __tablename__ = 'actions'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.LargeBinary, db.ForeignKey('users.id'))
    added = db.Column(db.Text)
    deleted = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())

    @staticmethod
    def prettify_rows(rows, small):
        """Преобразование списка строк в "опрятный" вид для рендера в таблице"""
        d = {}
        for i, row in enumerate(rows):
            added = deleted = ''
            if row.action == Action.ADD:
                action = 'add'
            elif row.action == Action.DELETE:
                action = 'delete'
            elif row.action == Action.REPLACE:
                action = 'replace'
            elif row.action == Action.BANNED:
                action = 'banned'
            elif row.action == Action.UNBANNED:
                action = 'unbanned'
            elif row.action == Action.TO_EDITOR:
                action = 'to_editor'
            elif row.action == Action.TO_SPECTATOR:
                action = 'to_spectator'
            if row.added is not None:
                added = row.added
            if row.deleted is not None:
                deleted = row.deleted
            user_id = User.query.filter(User.id == row.user_id).first().public_id

            if small:
                if user_id not in d:
                    d[user_id] = [[action, added, deleted, row.created_on]]
                elif d[user_id][-1][0] == action and d[user_id][-1][3] + datetime.timedelta(minutes=5) > row.created_on:
                    if action == 'add':
                        d[user_id][-1][1] = added + d[user_id][-1][1]
                        d[user_id][-1][3] = row.created_on
                    elif action == 'delete':
                        d[user_id][-1][2] = d[user_id][-1][2] + deleted
                        d[user_id][-1][3] = row.created_on
                    elif action == 'replace':
                        d[user_id][-1][1] += added
                        d[user_id][-1][2] = deleted + d[user_id][-1][2]
                        d[user_id][-1][3] = row.created_on
                else:
                    d[user_id].append([action, added, deleted, row.created_on])

        if small:
            rows = []
            for k, v in d.items():
                for e in v:
                    rows.append([k] + e)
        
        return rows
    