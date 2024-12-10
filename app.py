from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, UserData, UserCredentials
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session,flash  # Dodaj 'session'
import os


app = Flask(__name__)

# Konfiguracja bazy danych
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@LAPTOP-K4EC1DBK\\DAWID/TreningManager"
    "?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja bazy danych
db.init_app(app)

# Główna strona
@app.route('/')
def index():
    return render_template('index.html')

# Strona "O aplikacji"
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/Login')
def Login():
    return render_template('Login.html')

# Dodaj klucz sesji
app.secret_key = 'your_secret_key'  # Powinien być losowy i trudny do odgadnięcia

@app.route('/ask_details', methods=['GET', 'POST'])
def ask_details():
    if request.method == 'POST':
        user_data = request.form
        try:
            # Dodaj dane użytkownika do tabeli UserData
            new_user = UserData(
                first_name=user_data.get("first-name"),
                last_name=user_data.get("last-name"),
                age=int(user_data.get("age")),
                birth_date=user_data.get("birth-date"),
                height=float(user_data.get("height")),
                weight=float(user_data.get("weight")),
                discipline=user_data.get("discipline"),
            )
            db.session.add(new_user)

            # Dodaj dane logowania do tabeli UserCredentials
            new_credentials = UserCredentials(
                login=user_data.get("first-name"),
                password_hash=generate_password_hash(user_data.get("password")),
            )
            db.session.add(new_credentials)

            db.session.commit()

            # Zapisz imię użytkownika w sesji
            session['user_name'] = user_data.get("first-name")

            return redirect(url_for('main'))

        except SQLAlchemyError as e:
            db.session.rollback()  # Cofnięcie transakcji w razie błędu
            print(f"Błąd podczas zapisywania do bazy danych: {str(e)}")
            return "Wystąpił błąd podczas zapisywania danych. Sprawdź konsolę.", 500

    return render_template('ask_details.html')

# Strona logowania
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('first-name')  # Pobieranie loginu (imienia)
        password = request.form.get('password')  # Pobieranie hasła
        
        # Sprawdź dane logowania w tabeli UserCredentials
        user_credentials = UserCredentials.query.filter_by(login=login).first()

        if user_credentials and check_password_hash(user_credentials.password_hash, password):
            # Logowanie powiodło się
            session['user_name'] = login  # Zapisz login w sesji
            return redirect(url_for('main'))  # Przekierowanie na stronę 'main'
        else:
            # Niepoprawne dane logowania
            flash("Niepoprawne dane logowania. Spróbuj ponownie.", "error" )  # Wyświetl komunikat
            return redirect(url_for('login'))  # Powrót do strony logowania
    
    return render_template('login.html')


# Strona główna po zalogowaniu
@app.route('/main')
def main():
    return render_template('main.html')


# strona z boxing timer
@app.route('/Timer')
def boxing_timer():
    return render_template('Timer.html')

#strona z BMI
@app.route('/BMI')
def BMI():
    return render_template('BMI.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzenie tabel
    app.run(debug=True)
