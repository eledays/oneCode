from app import app, db, logger, socket, admin_id
from app.models import User, Action

from hashlib import sha256

from flask import request, render_template, make_response, session, redirect, jsonify, flash


@app.route('/admin')
def admin_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/admin_login')
    
    return render_template('admin.html')


@app.route('/admin_login', methods=['POST', 'GET'])
def admin_login_page():
    user_id = session.get('user_id')
    if user_id == admin_id:
        return redirect('/admin')
    
    if request.method == 'POST':
        password = request.form.get('password')
        print(sha256(password.encode()).hexdigest(), app.config.get('ADMIN_PASSWORD_HASH'))
        if sha256(password.encode()).hexdigest() == app.config.get('ADMIN_PASSWORD_HASH'):
            session['user_id'] = admin_id
            return redirect('/admin')
        else:
            return redirect('/')

    return render_template('admin_login.html')


@app.route('/admin/full_table')
def admin_full_table_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/admin_login')
    
    rows = db.session.query(Action).all()[::-1]
    rows = Action.prettify_rows(rows, False)
    
    return render_template('admin_table.html', rows=rows)


@app.route('/admin/table')
def admin_table_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/admin_login')
    
    rows = db.session.query(Action).all()[::-1]
    rows = Action.prettify_rows(rows, True)

    rows = sorted(rows, key=lambda x: x[4], reverse=True)
    
    return render_template('admin_table.html', rows=rows)


@app.route('/admin/users_table')
def admin_users_table_page():
    user_id = session.get('user_id')
    if user_id != admin_id:
        return redirect('/admin_login')
    
    rows = db.session.query(User).all()[::-1]
    
    return render_template('admin_users_table.html', rows=[[e.public_id, e.status] for e in rows])


@app.route('/admin/user/<user_id>')
def admin_user_page(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')
    
    if len(user_id) > 13:
        user = User.get_by_raw_id(user_id)
    else:
        user = db.session.query(User).filter(User.public_id == user_id).first()
    rows = db.session.query(Action).filter(Action.user_id == user.id).all()[::-1]
    rows = Action.prettify_rows(rows, True)

    return render_template('admin_user.html', user=user, rows=rows)


@app.route('/admin/change_update_time/<seconds>')
def change_update_time(seconds):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')
    
    if seconds.isdigit():
        app.config['SYMBOLS_UPDATING_TIME'] = int(seconds)

    return 'ok', 200


@app.route('/admin/change_symbols_count/<n>')
def change_symbols_count(n):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')
    
    if n.isdigit():
        app.config['DEFAULT_SYMBOLS_COUNT'] = int(n)

    return 'ok', 200


@app.route('/ban/<user_id>')
def ban(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')

    user = User.get_by_raw_id(user_id)
    try:
        user.ban()
        action = Action(action=Action.BANNED, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))

    return redirect(request.args.get('fr') or f'/admin/user/{user_id}')


@app.route('/unban/<user_id>')
def unban(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')

    user = User.get_by_raw_id(user_id)
    try:
        user.unban()
        action = Action(action=Action.UNBANNED, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))

    return redirect(request.args.get('fr') or f'/admin/user/{user_id}')


@app.route('/make_editor/<user_id>')
def make_editor(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')

    user = User.get_by_raw_id(user_id)
    try:
        user.make_editor()
        action = Action(action=Action.TO_EDITOR, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))

    return redirect(request.args.get('fr') or f'/admin/user/{user_id}')


@app.route('/make_all_spectator')
def make_all_spectator():
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')
    
    users = db.session.query(User).all()
    for user in users:
        try:
            user.make_spectator()
            action = Action(action=Action.TO_SPECTATOR, user_id=user.id)
            db.session.add(action)
            db.session.commit()
        except Exception as error:
            print(error)
            flash(str(error))
    return redirect('/admin/users_table')


@app.route('/make_spectator/<user_id>')
def make_spectator(user_id):
    page_user_id = session.get('user_id')
    if page_user_id != admin_id:
        return redirect('/admin_login')

    user = User.get_by_raw_id(user_id)
    try:
        user.make_spectator()
        action = Action(action=Action.TO_SPECTATOR, user_id=user.id)
        db.session.add(action)
        db.session.commit()
    except Exception as error:
        print(error)
        flash(str(error))

    return redirect(request.args.get('fr') or f'/admin/user/{user_id}')