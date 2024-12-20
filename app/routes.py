from app import app, db, logger
from app.models import User

import traceback
import sqlalchemy
from datetime import datetime, timedelta

from flask import request, render_template, make_response, session, redirect, jsonify

from difflib import SequenceMatcher


@app.route('/')
def index():
    user_id = session.get('user_id')
    
    if user_id is None:
        return render_template('auth.html')
    else:
        user_id = int(user_id, 16).to_bytes(16, 'big') if user_id else None
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            session.pop('user_id')
            return render_template('auth.html')
        else:
            return render_template('index.html', user_id=user.public_id)
        

@app.route('/save-fingerprint', methods=['POST'])
def save_fingerprint():
    r = request.json
    fingerprint = r.get('fingerprint')

    user_id = session.get('user_id')
    user_id = int(user_id, 16).to_bytes(16, 'big') if user_id else None

    fp_user = User.query.filter(User.fingerprint == fingerprint).first()
    id_user = User.query.filter(User.id == user_id).first()

    print(fp_user, id_user)

    if not fp_user and not id_user:
        try:
            for _ in range(100):
                user = User(fingerprint=fingerprint)
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


@app.route('/update_code', methods=['POST'])
def add_symbol():
    user_id = session.get('user_id')
    if user_id is None:
        return render_template('auth.html')
    
    user_id = int(user_id, 16).to_bytes(16, 'big') if user_id else None
    user = User.query.filter(User.id == user_id).first()
    
    data = request.json
    text = data.get('text')

    file = open(app.config.get('USER_CODE_PATH'), 'r+', encoding='utf-8')

    old_text = file.read()

    def calculate_diff(text1, text2):
        matcher = SequenceMatcher(None, text1, text2)
        total_changes = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                total_changes += (j2 - j1)
            elif tag == 'delete': 
                total_changes += (i2 - i1)
            elif tag == 'replace':
                total_changes += (i2 - i1) + (j2 - j1)
        
        return total_changes
    
    n = calculate_diff(old_text, text)
    if n > user.symbols:
        return jsonify({'error': 'Not enough symbols', 'text': old_text}), 400
    else:
        user.symbols -= n
        db.session.commit()
        
    file.seek(0)
    file.write(text)
    file.truncate()
    file.close()

    return jsonify({
        'text': text
    }), 200


@app.route('/get_symbols', methods=['GET'])
def get_symbols():
    user_id = session.get('user_id')
    if user_id is None:
        return render_template('auth.html')
    
    user_id = int(user_id, 16).to_bytes(16, 'big') if user_id else None
    user = User.query.filter(User.id == user_id).first()

    return jsonify({
        'symbols_left': user.symbols,
        'symbols_total': app.config.get('DEFAULT_SYMBOLS_COUNT')
    }), 200
