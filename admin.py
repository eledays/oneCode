from app import app, db
from app.models import User


with app.app_context():
    user_ids = [e.public_id for e in db.session.query(User)]


    print('user_ids:', ', '.join(user_ids))
    print('rm <user_id (>2 символов)> - удалить пользователя')
    print('add <user_id> <n=10> - добавить n символов')
    print('clr <user_id> - обнулить символы')


    cmd, user_id, *args = input().split()
    if len(user_id) <= 2:
        print('user_id must be > 2 symbols')
        exit()

    for e in user_ids:
        if str(e).startswith(user_id):
            user = db.session.query(User).filter(User.public_id == e).first()
            break
    else:
        print(f'user_id {user_id} not found')
        exit()
        

    if cmd == 'rm':
        if input('Please, enter full user_id: ') == user.public_id:
            db.session.delete(user)
            db.session.commit()
            print(f'user_id {e} deleted')
    elif cmd == 'add':
        if len(args) == 0:
            n = 10
        else:
            n = int(args[0])

        user.symbols += n
        db.session.commit()
        print(f'user_id {e} added {n} symbols')
    elif cmd == 'clr':
        user.symbols = 0
        db.session.commit()
        print(f'user_id {e} cleared')
    else:
        print('unknown command')
