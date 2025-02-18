import os
import firebase_admin
from firebase_admin import credentials, firestore

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT")
if SERVICE_ACCOUNT_PATH:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
else:
    # Alternatively, if you provide JSON content in an env var, you can load from that.
    cred = None

if not firebase_admin._apps:
    if cred:
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

db = firestore.client()
