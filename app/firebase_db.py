import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
if not SERVICE_ACCOUNT:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT environment variable is not set.")

try:
    if SERVICE_ACCOUNT.strip().startswith("{"):
        cred_info = json.loads(SERVICE_ACCOUNT)
        cred = credentials.Certificate(cred_info)
    else:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
except Exception as e:
    raise ValueError("Error loading Firebase service account credentials: " + str(e))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
