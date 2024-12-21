from app import app, db

import uuid
import random
import datetime


class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.LargeBinary, primary_key=True, default=uuid.uuid4().bytes)
    fingerprint = db.Column(db.Text)
    public_id = db.Column(db.Text, unique=True, default=hex(random.randint(16 ** 3, 16 ** 11)).lstrip('0x'))
    created_on = db.Column(db.DateTime, default=datetime.datetime.now())
    symbols = db.Column(db.Integer, default=app.config.get('DEFAULT_SYMBOLS_COUNT'))
    last_symbols_update = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return f'<User:{self.public_id}>'
    
    @staticmethod
    def get_by_raw_id(id):
        """Получение пользователя по байтовому id, который лежит в cookie"""

        if id is None:
            return None
        
        id = int(id, 16).to_bytes(16, 'big')
        user = User.query.filter(User.id == id).first()

        return user
    
