from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    districts = [
        ('aseliso', 'Aseliso@2024'),
        ('wahil', 'Wahil@2024'),
        ('biyoawale', 'Biyoawale@2024'),
        ('kelad', 'Kelad@2024')
    ]
    
    for username, new_pass in districts:
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = generate_password_hash(new_pass)
            print(f"Reset password for {username}")
        else:
            print(f"User {username} not found!")
    
    db.session.commit()
    print("All done!")