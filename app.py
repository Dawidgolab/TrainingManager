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
        existing_user = UserCredentials.query.filter_by(login=user_data.get("nick-name")).first()
        if existing_user:
            flash("Ten login (nick-name) jest już zajęty. Wybierz inny.", "error")
            return redirect(url_for('ask_details'))
        try:
            # Dodaj dane logowania do tabeli UserCredentials
            new_credentials = UserCredentials(
                login=user_data.get("nick-name"),
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
                nazwa=user_data.get("nick-name"),
                credentials_id=credentials_id  # Przypisanie poprawnego credentials_id
            )
            db.session.add(new_user)
            db.session.commit()

            # Zapisz imię użytkownika w sesji
            session['user_name'] = new_user.first_name

            return redirect(url_for('Login'))

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
        login = request.form.get('nick-name')
        password = request.form.get('password')
        
        user_credentials = UserCredentials.query.filter_by(login=login).first()
    

        if user_credentials and check_password_hash(user_credentials.password_hash, password):
            print("✅ Logowanie udane!")
            session['nick-name'] = login
            
            # Pobierz dane użytkownika
            user_data = UserData.query.filter_by(credentials_id=user_credentials.id).first()
            if user_data:
                session['user_name'] = user_data.first_name  # <- Dodaj to!

            return redirect(url_for('main'))
        else:
            print("❌ Błędne dane logowania.")
            flash("Niepoprawne dane logowania. Spróbuj ponownie.", "error")
            return redirect(url_for('login'))

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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby zobaczyć kalendarz.", "error")
        return redirect(url_for('login'))
    
    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

    if user:
        return render_template('Workout_plan.html')
    else:
        flash("Nie znaleziono użytkownika.", "error")
        return redirect(url_for('login'))

# Pobieranie ćwiczeń według wybranej kategorii
@app.route('/get_exercises', methods=['GET'])
def get_exercises():
    discipline = request.args.get("discipline")
    day_of_week = request.args.get("day_of_week")  # Pobranie dnia tygodnia

    if not discipline:
        return jsonify({"error": "Nie podano kategorii ćwiczeń"}), 400

    # Obsługuje przypadki, gdy dyscyplina to np. "chwytane i uderzane"
    if discipline == "chwytane i uderzane":
        filtered_exercises = [ex for ex in exercises_data["exercises"] if ex["discipline"] in ["chwytane", "uderzane"]]
    else:
        filtered_exercises = [ex for ex in exercises_data["exercises"] if ex["discipline"] == discipline]
    
    if not filtered_exercises:
        return jsonify({"error": "Brak ćwiczeń dla tej kategorii"}), 404
    
    # Przypisanie ćwiczeń do odpowiednich dni tygodnia
    if day_of_week in ['0', '2', '4']:  # Poniedziałek, Środa, Piątek
        filtered_exercises = [ex for ex in filtered_exercises if ex["type"] == "technika"]
    elif day_of_week in ['1', '3']:  # Wtorek, Czwartek
        filtered_exercises = [ex for ex in filtered_exercises if ex["type"] == "siłowe"]
    elif day_of_week == '5':  # Sobota
        filtered_exercises = [ex for ex in filtered_exercises if ex["type"] == "interwały"]
    elif day_of_week == '6':  # Niedziela
        return jsonify([])  # Dzień wolny
    
    # Losowanie 5 ćwiczeń
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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby zobaczyć kalendarz.", "error")
        return redirect(url_for('login'))

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby zapisać trening.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby dodać trening.", "error")
        return redirect(url_for('login'))

    # Pobierz dane z formularza
    training_date = request.form['training_date']
    training_type = request.form['training_type']

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

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
    if 'nick-name' not in session:
        return jsonify({'success': False, 'message': 'Musisz być zalogowany, aby usunąć trening.'})

    training_date = request.form['training_date']
    print(f"Trening do usunięcia: {training_date}")  # Logowanie daty treningu

    # Pobierz użytkownika na podstawie loginu
    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby korzystać z notatnika.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(nazwa=session['nick-name']).first()
    if not user:
        flash("Nie znaleziono użytkownika.", "error")
        return redirect(url_for('main'))

    # Pobieramy tylko notatki zalogowanego użytkownika
    notes = Notepad.query.filter_by(user_id=user.id).all()

    return render_template('Notepad.html', notes=notes)  # 👈 Notatki są przekazywane do HTML



@app.route('/save_note', methods=['POST'])
def save_note():
    if 'nick-name' not in session:
        return jsonify({'success': False, 'message': 'Musisz być zalogowany, aby zapisać notatkę.'})

    user = UserData.query.filter_by(nazwa=session['nick-name']).first()
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
    if 'nick-name' not in session:
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
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby korzystać z tej funkcji.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(nazwa=session['nick-name']).first()


    return render_template('Daily_workout.html', user=user)


###########################################################################################

#Moje dane
@app.route('/myData')
def MyData():
    if 'nick-name' not in session:
        flash("Musisz być zalogowany, aby zobaczyć swoje dane.", "error")
        return redirect(url_for('login'))

    user = UserData.query.filter_by(nazwa=session['nick-name']).first()

    if not user:
        flash("Nie znaleziono danych użytkownika.", "error")
        return redirect(url_for('main'))


    return render_template('myData.html', user=user)





###########################################################################################
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tworzenie tabel
    app.run(debug=True)
