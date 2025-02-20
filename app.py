from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, UserData, UserCredentials
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session,flash  # Dodaj 'session'
from flask_migrate import Migrate
import random
import json

app = Flask(__name__)

# Konfiguracja bazy danych
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@LAPTOP-K4EC1DBK\\DAWID/TreningManager"
    "?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicjalizacja bazy danych
db.init_app(app)

migrate = Migrate(app, db)

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
            # Dodaj dane logowania do tabeli UserCredentials
            new_credentials = UserCredentials(
                login=user_data.get("first-name"),
                password_hash=generate_password_hash(user_data.get("password")),
            )
            db.session.add(new_credentials)
            db.session.commit()

            # Pobierz ID nowo dodanych danych logowania
            credentials_id = new_credentials.id

            # Dodaj dane użytkownika do tabeli UserData
            new_user = UserData(
                first_name=user_data.get("first-name"),
                last_name=user_data.get("last-name"),
                age=int(user_data.get("age")),
                discipline=user_data.get("discipline"),
                credentials_id=credentials_id,  # Przypisanie poprawnego credentials_id
                level=1  # Ustaw domyślny poziom
            )
            db.session.add(new_user)
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





# Wczytaj dane ćwiczeń z pliku JSON
with open("Exercises.json", encoding="utf-8") as f:
    exercises_data = json.load(f)

# Strona z generowaniem planów treningowych
@app.route('/Workout_plan')
def workout_plan():
    return render_template('Workout_plan.html')


@app.route('/get_exercises', methods=['GET'])
def get_exercises():
    filtered_exercises = [ex for ex in exercises_data["exercises"] if ex["discipline"] == "chwytane"]
    
    if not filtered_exercises:
        return jsonify({"error": "Brak ćwiczeń dla tej kategorii"}), 404
    
    selected_exercises = random.sample(filtered_exercises, min(len(filtered_exercises), 5))
    
    return jsonify(selected_exercises)





# strona z boxing timer
@app.route('/Timer')
def boxing_timer():
    return render_template('Timer.html')

#strona z BMI i zapotrzebowaniem kalorycznym 
@app.route('/BMI')
def BMI():
    return render_template('BMI.html')

#strona z Kalendarzem
@app.route('/Calendar')
def Calendar():
    return render_template('Calendar.html')

#strona z Notatnikiem
@app.route('/Notepad')
def Notepad():
    return render_template('Notepad.html')

# Codzienna motywacja/Ćwiczenia
@app.route('/Daily_workout', methods=['GET', 'POST'])
def Daily_workout():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby korzystać z tej funkcji.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if request.method == 'POST':
        # Przykładowa logika aktualizacji poziomu
        points_gained = 10  # Punkty zdobyte za ukończenie treningu
        points_for_next_level = 50  # Punkty wymagane do awansu na kolejny poziom

        # Oblicz nowy poziom
        if user:
            user.level += points_gained // points_for_next_level  # Zwiększ poziom na podstawie punktów
            db.session.commit()  # Zapisz zmiany w bazie danych

        flash(f"Gratulacje! Twój nowy poziom to {user.level}.", "success")
        return redirect(url_for('Daily_workout'))

    return render_template('Daily_workout.html', user=user)



#Moje dane
@app.route('/myData')
def MyData():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby zobaczyć swoje dane.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if not user:
        flash("Nie znaleziono danych użytkownika.", "error")
        return redirect(url_for('main'))

    # Odśwież dane użytkownika w sesji
    session['user_level'] = user.level
    return render_template('myData.html', user=user)



@app.route('/update', methods=['POST'])
def update_level():
    if 'user_name' not in session:
        return jsonify({"error": "User not logged in"}), 400

    user_name = request.form.get('user_name')
    new_level = request.form.get('level')

    user = UserData.query.filter_by(first_name=user_name).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Zaktualizuj poziom użytkownika w bazie danych
        user.level = new_level
        db.session.commit()  # Zapisz zmiany w bazie danych
        return jsonify({"message": "Level updated successfully"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzenie tabel
    app.run(debug=True)
