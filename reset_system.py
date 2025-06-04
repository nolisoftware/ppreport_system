import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_system():
    # Close any existing connections
    db.session.close()
    
    # Delete old database
    db_path = os.path.join(app.instance_path, 'reports.db')
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        print("Please close all programs using the database and try again")
        return

    # Create fresh database
    with app.app_context():
        db.create_all()

        # Add all users
        users = [
            # Main Office
            {
                'username': 'main_office',
                'password': 'main123',
                'district': 'Main Office',
                'is_main_office': True
            },
            # Standard Woredas 1-9
            *[{
                'username': f'woreda{i}',
                'password': f'woreda{i}pass',
                'district': f'ወረዳ {i}',
                'is_main_office': False
            } for i in range(1, 10)],
            # Special Woredas
            {
                'username': 'aseliso',
                'password': 'Aseliso@2024',
                'district': 'አሰሊሶ',
                'is_main_office': False
            },
            {
                'username': 'biyoawale',
                'password': 'Biyoawale@2024',
                'district': 'ቢዮአዋሌ',
                'is_main_office': False
            },
            {
                'username': 'wahil',
                'password': 'Wahil@2024',
                'district': 'ዋሂል',
                'is_main_office': False
            },
            {
                'username': 'kelad',
                'password': 'Kelad@2024',
                'district': 'ቀልአድ',
                'is_main_office': False
            }
        ]

        # Clear and repopulate users
        User.query.delete()
        for user_data in users:
            db.session.add(User(
                username=user_data['username'],
                password=generate_password_hash(user_data['password']),
                district=user_data['district'],
                is_main_office=user_data['is_main_office']
            ))
        
        db.session.commit()
        print("Success! Database reset with all 14 accounts")

if __name__ == '__main__':
    reset_system()