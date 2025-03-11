from models import db, UserData, UserCredentials, CalendarWorkout, Notepad
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session,flash,jsonify  # Dodaj 'session'
from flask_migrate import Migrate
import random
import json
###########################################################################################



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



###########################################################################################

# Główna strona
@app.route('/')
def index():
    return render_template('index.html')

###########################################################################################

# Strona "O aplikacji"
@app.route('/about')
def about():
    return render_template('about.html')

###########################################################################################

@app.route('/Login')
def Login():
    return render_template('Login.html')

###########################################################################################


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

###########################################################################################

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




@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Usuwa całą sesję użytkownika
    flash("Zostałeś wylogowany.", "info")
    return redirect(url_for('index'))  # Przekierowanie na stronę główną


###########################################################################################

# Strona główna po zalogowaniu
@app.route('/main')
def main():
    return render_template('main.html')

###########################################################################################



# Wczytaj dane ćwiczeń z pliku JSON
with open("Exercises.json", encoding="utf-8") as f:
    exercises_data = json.load(f)

###########################################################################################

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


###########################################################################################


# strona z boxing timer
@app.route('/Timer')
def boxing_timer():
    return render_template('Timer.html')
###########################################################################################

#strona z BMI i zapotrzebowaniem kalorycznym 
@app.route('/BMI')
def BMI():
    return render_template('BMI.html')

###########################################################################################
#strona z Kalendarzem


@app.route('/Calendar')
def Calendar():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby zobaczyć kalendarz.", "error")
        return redirect(url_for('login'))

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if user:
        # Pobierz wszystkie zapisane treningi dla tego użytkownika
        workouts = CalendarWorkout.query.filter_by(user_id=user.id).all()

        # Zamień obiekty CalendarWorkout na listę słowników z datami i notatkami
        workout_dates = [{"date_workout": workout.date_workout, "note": workout.note} for workout in workouts]

        return render_template('Calendar.html', workouts=workout_dates)
    else:
        flash("Nie znaleziono użytkownika.", "error")
        return redirect(url_for('login'))



@app.route('/add_training', methods=['POST'])
def add_training():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby zapisać trening.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if not user:
        flash("Nie znaleziono danych użytkownika.", "error")
        return redirect(url_for('main'))

    training_date = request.form.get('training-date')
    training_type = request.form.get('training-type')

    # Debugowanie: Wypisanie danych otrzymanych z formularza
    print(f"Training Date: {training_date}, Training Type: {training_type}")

    # Sprawdzenie, czy trening już istnieje na wybrany dzień
    existing_training = CalendarWorkout.query.filter_by(user_id=user.id, date_workout=training_date).first()
    if existing_training:
        flash("Trening na tę datę już istnieje!", "error")
        return redirect(url_for('Calendar'))

    new_training = CalendarWorkout(
        user_id=user.id,
        date_workout=training_date,
        note=training_type
    )

    try:
        db.session.add(new_training)
        db.session.commit()
        flash("Trening zapisany!", "success")
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback in case of error
        flash("Wystąpił błąd podczas zapisywania treningu.", "error")
        print(f"Error: {str(e)}")

    return redirect(url_for('Calendar'))




def save_training():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby dodać trening.", "error")
        return redirect(url_for('login'))

    # Pobierz dane z formularza
    training_date = request.form['training_date']
    training_type = request.form['training_type']

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if user:
        # Zapisz trening w bazie danych
        new_training = CalendarWorkout(
            user_id=user.id,
            date_workout=training_date,
            note=training_type
        )
        db.session.add(new_training)
        db.session.commit()

        flash("Trening został zapisany!", "success")
        return redirect(url_for('Calendar'))  # Przekierowanie do kalendarza
    else:
        flash("Użytkownik nie znaleziony!", "error")
        return redirect(url_for('login'))


@app.route('/delete_training', methods=['POST'])
def delete_training():
    # Sprawdzamy, czy użytkownik jest zalogowany
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Musisz być zalogowany, aby usunąć trening.'})

    training_date = request.form['training_date']
    print(f"Trening do usunięcia: {training_date}")  # Logowanie daty treningu

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(first_name=session['user_name']).first()

    if user:
        # Znajdź trening w bazie danych na podstawie daty i użytkownika
        training = CalendarWorkout.query.filter_by(user_id=user.id, date_workout=training_date).first()

        if training:
            db.session.delete(training)
            db.session.commit()
            print(f"Trening z datą {training_date} został usunięty.")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Trening nie istnieje.'})
    else:
        return jsonify({'success': False, 'message': 'Użytkownik nie znaleziony.'})
    

###########################################################################################


#strona z Notatnikiem
@app.route('/Notepad')
def notepad():
    if 'user_name' not in session:
        flash("Musisz być zalogowany, aby korzystać z notatnika.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(first_name=session['user_name']).first()
    if not user:
        flash("Nie znaleziono użytkownika.", "error")
        return redirect(url_for('main'))

    # Pobieramy tylko notatki zalogowanego użytkownika
    notes = Notepad.query.filter_by(user_id=user.id).all()

    return render_template('Notepad.html', notes=notes)  # 👈 Notatki są przekazywane do HTML



@app.route('/save_note', methods=['POST'])
def save_note():
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Musisz być zalogowany, aby zapisać notatkę.'})

    user = UserData.query.filter_by(first_name=session['user_name']).first()
    if not user:
        return jsonify({'success': False, 'message': 'Nie znaleziono użytkownika.'})

    note_text = request.json.get('note_text', '').strip()
    if not note_text:
        return jsonify({'success': False, 'message': 'Treść notatki nie może być pusta.'})

    # Tworzymy nową notatkę przypisaną do konkretnego użytkownika
    new_note = Notepad(user_id=user.id, note_text=note_text)
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Notatka zapisana!', 'note_id': new_note.id})



@app.route('/delete_note', methods=['POST'])
def delete_note():
    if 'user_name' not in session:
        return jsonify({'success': False, 'message': 'Musisz być zalogowany, aby usunąć notatkę.'})

    note_id = request.json.get('note_id')
    note = Notepad.query.get(note_id)

    if not note:
        return jsonify({'success': False, 'message': 'Notatka nie istnieje.'})

    db.session.delete(note)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Notatka usunięta!'})



###########################################################################################

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


###########################################################################################

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


    return render_template('myData.html', user=user)





###########################################################################################
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzenie tabel
    app.run(debug=True)
