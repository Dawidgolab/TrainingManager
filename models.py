from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Inicjalizacja SQLAlchemy
db = SQLAlchemy()

# Model danych
class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    discipline = db.Column(db.String(100), nullable=False)
    credentials_id = db.Column(db.Integer, db.ForeignKey('user_credentials.id'))  # Powiązanie z UserCredentials
    level = db.Column(db.Integer, nullable=False, default=1) 
    
    def __repr__(self):
        return f"<User {self.first_name} {self.last_name}>"

class UserCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_data = db.relationship('UserData', backref='credentials', uselist=False)  # Relacja 1:1

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<UserCredentials {self.login}>"


class CalendarWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.id'), nullable=False)
    date_workout = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(100))

    user = db.relationship('UserData', backref=db.backref('workouts', lazy=True))

    def __repr__(self):
        return f"<Workout {self.date_workout} - {self.note}>"



class Notepad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.id'), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    # created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('UserData', backref=db.backref('notes', lazy=True))
