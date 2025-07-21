from backend.firebase_config import db

def user_exists(email: str):
    doc = db.collection("users").document(email).get()
    return doc.to_dict().get("password") if doc.exists else None

def create_user(email: str, password: str):
    db.collection("users").document(email).set({
        "email": email,
        "password": password
    })
