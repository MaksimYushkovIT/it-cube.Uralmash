from app import create_app, db
from app.models import User, Group
from werkzeug.security import generate_password_hash
import random

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            hashed_password = generate_password_hash('admin')
            admin = User(username='admin', full_name='Administrator', email='admin@example.com', password_hash=hashed_password, role='admin', is_confirmed=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

        # Создание группы для учеников
        group = Group.query.filter_by(name='Default Group').first()
        if not group:
            group = Group(name='Default Group')
            db.session.add(group)
            db.session.commit()
            print("Default group created successfully.")
        else:
            print("Default group already exists.")

        # Создание 10 учеников
        for i in range(1, 11):
            student = User.query.filter_by(email=f'student{i}@example.com').first()
            if not student:
                hashed_password = generate_password_hash(f'student{i}')
                student = User(
                    username=f'student{i}',
                    full_name=f'Student {i}',
                    email=f'student{i}@example.com',
                    password_hash=hashed_password,
                    role='student',
                    group=group,
                    points=random.randint(0, 100),
                    is_confirmed=True
                )
                db.session.add(student)
                db.session.commit()
                print(f"Student {i} created successfully.")
            else:
                print(f"Student {i} already exists.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)