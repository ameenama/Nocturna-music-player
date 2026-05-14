from app import app, db, User

with app.app_context():
    admin = User(username='admin', password='admin123', status='active')
    db.session.add(admin)
    db.session.commit()
    print('Admin created successfully!')