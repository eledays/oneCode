from app import app, db

import uuid
import random
import datetime

from pprint import pprint


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.LargeBinary, primary_key=True, default=uuid.uuid4().bytes)
    fingerprint = db.Column(db.Text)
    public_id = db.Column(db.Text, unique=True, default=hex(random.randint(16 ** 3, 16 ** 11)).lstrip('0x'))
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    symbols = db.Column(db.Integer, default=app.config.get('DEFAULT_SYMBOLS_COUNT'))
    last_symbols_update = db.Column(db.DateTime, default=datetime.datetime.now())
    banned = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User:{self.public_id}>'
    
    @staticmethod
    def get_by_raw_id(id):
        """Получение пользователя по байтовому id в hex формате, который лежит в cookie"""

        if id is None:
            return None
        
        id = int(id, 16).to_bytes(16, 'big')
        user = User.query.filter(User.id == id).first()

        return user
    

class Action(db.Model):

    ADD = 0
    DELETE = 1
    REPLACE = 2
    BANNED = 3
    UNBANNED = 4

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
            if row.action == Action.ADD:
                row.action = 'add'
            elif row.action == Action.DELETE:
                row.action = 'delete'
            elif row.action == Action.REPLACE:
                row.action = 'replace'
            elif row.action == Action.BANNED:
                row.action = 'banned'
            elif row.action == Action.UNBANNED:
                row.action = 'unbanned'
            if row.added is None:
                row.added = ''
            if row.deleted is None:
                row.deleted = ''
            row.user_id = row.user_id.hex()

            if small:
                if row.user_id not in d:
                    d[row.user_id] = [[row.action, row.added, row.deleted, row.created_on]]
                elif d[row.user_id][-1][0] == row.action and d[row.user_id][-1][3] + datetime.timedelta(minutes=5) > row.created_on:
                    if row.action == 'add':
                        d[row.user_id][-1][1] = row.added + d[row.user_id][-1][1]
                    elif row.action == 'delete':
                        d[row.user_id][-1][2] = d[row.user_id][-1][2] + row.deleted
                    elif row.action == 'replace':
                        d[row.user_id][-1][1] += row.added
                        d[row.user_id][-1][2] = row.deleted + d[row.user_id][-1][2]
                else:
                    d[row.user_id].append([row.action, row.added, row.deleted, row.created_on])

                # print(d)

                # if i > 0 and row.user_id == rows[i - 1].user_id and row.action == rows[i - 1].action == 'add':
                #     row.added = row.added + rows[i - 1].added
                #     rows[i - 1] = None
                # elif i > 0 and row.user_id == rows[i - 1].user_id and row.action == rows[i - 1].action == 'delete':
                #     row.deleted =  rows[i - 1].deleted + row.deleted
                #     rows[i - 1] = None

                
        # rows = list(filter(lambda x: x is not None, rows))

        # pprint([[[k] + e for e in v] for k, v in d.items()][0])

        if small:
            return [[[k] + e for e in v] for k, v in d.items()][0]
        else:
            return rows
    