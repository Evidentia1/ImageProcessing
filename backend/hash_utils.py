import hashlib
from backend.firebase_config import db

def compute_sha256(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return file_hash

def check_duplicate_hash(file_hash):
    hashes_ref = db.collection("image_hashes")
    docs = hashes_ref.where("hash", "==", file_hash).stream()
    return any(True for _ in docs)
