from app import app, db, logger, socket, admin_id
from app.models import User, Action

import traceback
import sqlalchemy
from datetime import datetime, timedelta

from flask import request, render_template, make_response, session, redirect, jsonify, flash
from flask_socketio import emit

from difflib import SequenceMatcher


@app.route('/')
def index():
    user_id = session.get('user_id')
    
    if user_id is None:
        return render_template('auth.html')
    
    user = User.get_by_raw_id(user_id)
    if user is None:
        session.pop('user_id')
        return render_template('auth.html')
    elif user.banned:
        return render_template('banned.html')
    else:
        return render_template('index.html', user_id=user.public_id)
        

@app.route('/save-fingerprint', methods=['POST'])
def save_fingerprint():
    r = request.json
    fingerprint = r.get('fingerprint')

    user_id = session.get('user_id')
    id_user = User.get_by_raw_id(user_id)

    fp_user = User.query.filter(User.fingerprint == fingerprint).first()

    if (id_user is not None and id_user.banned) or (fp_user is not None and fp_user.banned):
        logger.log(f'Banned user tried to login', request.remote_addr)
        return jsonify({'error': 'User is banned'}), 400

    if not fp_user and not id_user:
        try:
            for _ in range(100):
                user = User(fingerprint=fingerprint)
                print(user)
                try:
                    db.session.add(user)
                    db.session.commit()
                    break
                except sqlalchemy.exc.IntegrityError:
                    user = User(fingerprint=fingerprint)
                    continue

            logger.log(f'Created {user}', request.remote_addr)

            session['user_id'] = user.id.hex()
            return jsonify({}), 200
        
        except Exception as error:
            exc = traceback.format_exc()
            logger.log(f'Error while creating user: {error}', request.remote_addr)
            print(exc)
            return jsonify({'error': str(error)}), 400
    
    elif fp_user and not id_user:
        if datetime.now() > fp_user.created_on + timedelta(hours=1):
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


@app.route('/admin/<user_id>')
def admin(user_id):
    if user_id == admin_id:
        session['user_id'] = admin_id
        return redirect('/admin')
    
    return redirect('/')


@app.route('/admin')
def admin_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/')
    
    return render_template('admin.html')


@app.route('/admin/full_table')
def admin_full_table_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/')
    
    rows = db.session.query(Action).all()[::-1]
    rows = Action.prettify_rows(rows, False)
    
    return render_template('admin_table.html', rows=rows)


@app.route('/admin/table')
def admin_table_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/')
    
    rows = db.session.query(Action).all()[::-1]
    rows = Action.prettify_rows(rows, True)
    
    return render_template('admin_table.html', rows=rows)


@app.route('/admin/user/<user_id>')
def admin_user_page(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/')
    
    user = User.get_by_raw_id(user_id)
    rows = db.session.query(Action).filter(Action.user_id == user.id).all()[::-1]
    rows = Action.prettify_rows(rows, True)

    return render_template('admin_user.html', user=user, rows=rows)


@app.route('/ban/<user_id>')
def ban(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/')

    user = User.get_by_raw_id(user_id)
    try:
        user.banned = True
        action = Action(action=Action.BANNED, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))
    return redirect(f'/admin/user/{user_id}')


@app.route('/unban/<user_id>')
def unban(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/')

    user = User.get_by_raw_id(user_id)
    try:
        user.banned = False
        action = Action(action=Action.UNBANNED, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))
    return redirect(f'/admin/user/{user_id}')


@socket.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    user = User.get_by_raw_id(user_id)

    if user is None:
        return {'error': 'No user_id'}
    
    if user.banned:
        return {'error': 'User is banned'}

    
    with open(app.config.get('USER_CODE_PATH'), 'r', encoding='utf-8') as file:
        code = file.read()
    emit('update_client', {
        'code': code,
        'symbols': {
            'left': user.symbols,
            'total': app.config.get('DEFAULT_SYMBOLS_COUNT'),
            'update_in': (user.last_symbols_update + timedelta(seconds=app.config.get('SYMBOLS_UPDATING_TIME')) - datetime.now()).total_seconds(),
        }
    })


@socket.on('update_server_code')
def handle_update_server_code(text):
    user_id = session.get('user_id')
    user = User.get_by_raw_id(user_id)
    if user is None:
        return {'error': 'No user_id'}
    
    if user.banned:
        return {'error': 'User is banned'}

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
    
    n, action, added, deleted = calculate_diff(old_text, text)
    if n > user.symbols:
        text = old_text
        error = 'Not enough symbols'
    else:
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
    if user.banned:
        return {'error': 'User is banned'}
    
    with open(app.config.get('USER_CODE_PATH'), 'r', encoding='utf-8') as file:
        code = file.read()

    emit('update_client', code)