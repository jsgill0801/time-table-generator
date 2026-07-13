from backend.db import init_db, get_db
from backend.services.auth_service import create_user
from backend.models.user import User

def main():
    print('Initialising DB...')
    init_db()

    db = next(get_db())
    try:
        admin = db.query(User).filter(User.role == 'admin').first()
        if admin:
            print('Admin already exists:', admin.username)
            return

        create_user(db, 'admin', 'admin@local', 'admin123', role='admin')
        print('Admin user created: admin')

    except Exception as e:
        print('Error creating admin:', e)

    finally:
        db.close()

if __name__ == '__main__':
    main()
