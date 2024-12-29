from app import app, db, logger, socket, admin_id
from app.models import User, Action

import traceback
import sqlalchemy
from datetime import datetime, timedelta
import random
import uuid

from flask import request, render_template, make_response, session, redirect, jsonify, flash
from flask_socketio import emit

from difflib import SequenceMatcher


@app.route('/')
def index():
    user_id = session.get('user_id')
    
    if user_id is None:
        return render_template('auth.html')
    elif user_id == admin_id:
        return render_template('index.html', can_edit=False)
    
    user = User.get_by_raw_id(user_id)
    if 'authed' in request.args and user is None:
        return redirect('/error/auth_error')
    if user is None:
        session.pop('user_id')
        return render_template('auth.html')
    elif user.is_banned():
        return render_template('banned.html')
    else:
        return render_template('index.html', user_id=user.public_id, can_edit=user.is_editor(), first='first' in request.args)
        

@app.route('/save-fingerprint', methods=['POST'])
def save_fingerprint():
    r = request.json
    fingerprint = r.get('fingerprint')

    user_id = session.get('user_id')
    id_user = User.get_by_raw_id(user_id)

    fp_user = User.query.filter(User.fingerprint == fingerprint).first()

    if (id_user is not None and id_user.is_banned()) or (fp_user is not None and fp_user.is_banned):
        logger.log(f'Banned user {id_user or fp_user} tried to login', request.remote_addr)
        if fp_user is not None:
            fp_user.created_on = datetime.now()
            db.session.commit()
            id_user = fp_user
        session['user_id'] = id_user.id.hex()
        return jsonify({'error': 'User is banned'}), 400

    if not fp_user and not id_user:
        try:
            for _ in range(100):
                user = User(id=uuid.uuid4().bytes, fingerprint=fingerprint, public_id=hex(random.randint(16 ** 3, 16 ** 11)).lstrip('0x'))
                try:
                    db.session.add(user)
                    db.session.commit()
                    break
                except sqlalchemy.exc.IntegrityError:
                    db.session.rollback()
                    user = User(id=uuid.uuid4().bytes, fingerprint=fingerprint, public_id=hex(random.randint(16 ** 3, 16 ** 11)).lstrip('0x'))
                    continue

            logger.log(f'Created {user}', request.remote_addr)

            session['user_id'] = user.id.hex()
            return jsonify({'new_user': True}), 200
        
        except Exception as error:
            exc = traceback.format_exc()
            logger.log(f'Error while creating user: {error}', request.remote_addr)
            print(exc)
            return jsonify({'error': str(error)}), 400
    
    elif fp_user and not id_user:
        if datetime.now() > fp_user.created_on + app.config.get('COOKIE_UPDATE_TIMEOUT'):
            logger.log(f'FP updated for {fp_user} (no cookie, old profile)', request.remote_addr)
            fp_user.fingerprint = fingerprint
            fp_user.created_on = datetime.now()
            db.session.commit()
            id_user = fp_user
        else:
            logger.log(f'Cookie-error with {fp_user}', request.remote_addr)
            return jsonify({'error': 'cookie-error'}), 400
    
    elif not fp_user and id_user or id_user is not fp_user:
        logger.log(f'FP updated for {id_user}'), request.remote_addr
        id_user.fingerprint = fingerprint
        db.session.commit()
    
    session['user_id'] = id_user.id.hex()
    logger.log(f'Successful authorization {id_user}', request.remote_addr)
    return jsonify({}), 200


@app.route('/error/<error>')
def error_page(error):
    return render_template('error.html', error=error)


@socket.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    user = User.get_by_raw_id(user_id)

    if user is None and user_id != admin_id:
        return {'error': 'No user_id'}
    
    if user and user.is_banned():
        return {'error': 'User is banned'}

    
    with open(app.config.get('USER_CODE_PATH'), 'r', encoding='utf-8') as file:
        code = file.read()

    if user:
        data = {
            'code': code,
            'symbols': {
                'left': user.symbols,
                'total': app.config.get('DEFAULT_SYMBOLS_COUNT'),
                'update_in': (user.last_symbols_update + timedelta(seconds=app.config.get('SYMBOLS_UPDATING_TIME')) - datetime.now()).total_seconds(),
            }
        }
    else:
        data = {'code': code}

    emit('update_client', data)


@socket.on('update_server_code')
def handle_update_server_code(text):
    user_id = session.get('user_id')

    if user_id == admin_id:
        with open(app.config.get('USER_CODE_PATH'), 'w', encoding='utf-8') as file:
            file.write(text)
            emit('update_client', {
                'code': text,
            }, broadcast=True)
        return {'test': text}
    else:
        user = User.get_by_raw_id(user_id)

    if user is None:
        return {'error': 'No user_id'}
    
    if user.is_banned():
        return {'error': 'User is banned'}
    
    if user.is_spectator():
        with open(app.config.get('USER_CODE_PATH'), 'r+', encoding='utf-8') as file:
            return {'error': 'User is spectator', 'text': file.read()}

    if datetime.now() > user.last_symbols_update + timedelta(seconds=app.config.get('SYMBOLS_UPDATING_TIME')):
        user.symbols = app.config.get('DEFAULT_SYMBOLS_COUNT')
        user.last_symbols_update = datetime.now()
        db.session.commit()

    file = open(app.config.get('USER_CODE_PATH'), 'r+', encoding='utf-8')

    old_text = file.read()

    def calculate_diff(text1, text2):
        matcher = SequenceMatcher(None, text1, text2)
        r = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                r = (j2 - j1, Action.ADD, text2[j1:j2], None)
            elif tag == 'delete':
                r = (i2 - i1, Action.DELETE, None, text1[i1:i2])
            elif tag == 'replace':
                r = (i2 - i1, Action.REPLACE, text2[j1:j2], text1[i1:i2])

        return r
    
    diff = calculate_diff(old_text, text)
    if diff is None:
        return
    n, action, added, deleted = calculate_diff(old_text, text)
    if n > user.symbols:
        text = old_text
        error = 'Not enough symbols'
    else:
        n -= (added.count(' ') if added else 0 + deleted.count(' ') if deleted else 0)
        user.symbols -= n
        if user.last_symbols_update + timedelta(seconds=app.config.get('SYMBOLS_UPDATING_TIME')) < datetime.now():
            user.last_symbols_update = datetime.now()

        action = Action(
            action=action, 
            user_id=user.id,
            added=added,
            deleted=deleted
        )
        db.session.add(action)
        db.session.commit()
        
        file.seek(0)
        file.write(text)
        file.truncate()

        error = None
        
    file.close()

    emit('update_client', {
        'code': text,
    }, broadcast=True)
    emit('update_client', {'symbols': {
            'left': user.symbols,
            'total': app.config.get('DEFAULT_SYMBOLS_COUNT'),
            'update_in': (user.last_symbols_update + timedelta(seconds=app.config.get('SYMBOLS_UPDATING_TIME')) - datetime.now()).total_seconds(),
        }
    })

    return {'code': text, 'error': error}


@socket.on('update_client')
def handle_update_client():
    user_id = session.get('user_id')
    if user_id is None:
        return render_template('auth.html')
    
    user = User.get_by_raw_id(user_id)
    if user.is_banned():
        return {'error': 'User is banned'}
    
    with open(app.config.get('USER_CODE_PATH'), 'r', encoding='utf-8') as file:
        code = file.read()

    emit('update_client', code)