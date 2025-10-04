import firebase_admin
from firebase_admin import credentials, auth
import os

# --- Configuration ---
# The path to your service account JSON file
SERVICE_ACCOUNT_FILE = 'firebase_creds.json'

# The user ID (uid) you want to create a token for.
# This will become the localpart of the Matrix ID (@uid:server.name)
# This user does NOT have to exist in Firebase Auth beforehand.
USER_ID_TO_TEST = "testuser123"
# --- End Configuration ---

# Check if the service account file exists
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    print(f"Error: Service account file not found at '{SERVICE_ACCOUNT_FILE}'")
    exit(1)

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred)

# Create the custom token
try:
    custom_token = auth.create_custom_token(USER_ID_TO_TEST)
    print("✅ Successfully created Firebase Custom Token!")
    print("\nThis is a CUSTOM token. You must now exchange it for an ID token.")
    print("Use a command like the one below (you'll need your Web API Key):\n")
    print(f"curl -X POST -H 'Content-Type: application/json' -d '{{\"token\":\"{custom_token.decode('utf-8')}\",\"returnSecureToken\":true}}' 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyCVm85lgzoq2Tkb76ecAr4rjbjUBDf-DfM'")

except Exception as e:
    print(f"Error creating custom token: {e}")
