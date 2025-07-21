import firebase_admin
from firebase_admin import credentials, firestore, storage
from pathlib import Path

# Path to your service account key inside backend folder
cred = credentials.Certificate(Path(__file__).parent / "firebase_key.json")

firebase_admin.initialize_app(cred, {
    'storageBucket': 'insurance-claim-75eea.firebasestorage.app'  # replace with your actual bucket name
})

# Firestore DB
db = firestore.client()

# Firebase Storage
bucket = storage.bucket()
