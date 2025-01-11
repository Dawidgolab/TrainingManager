from app import app, db, UserData, UserCredentials

# Uruchomienie kontekstu aplikacji Flask
with app.app_context():
    # Zaktualizuj rekordy z NULL w kolumnie 'level'
    db.session.query(UserData).filter(UserData.level == None).update({UserData.level: 1})
    
    # Zaktualizuj rekordy z NULL w kolumnie 'credentials_id'
    users_with_null_credentials = UserData.query.filter(UserData.credentials_id == None).all()
    
    for user in users_with_null_credentials:
        # Znajdź odpowiednie dane logowania na podstawie imienia
        user_credentials = UserCredentials.query.filter_by(login=user.first_name).first()
        
        if user_credentials:
            user.credentials_id = user_credentials.id
            db.session.commit()
    
    # Zapisz zmiany w bazie danych
    db.session.commit()

    print("Poziomy użytkowników oraz credentials_id zostały zaktualizowane.")
