import logging
from typing import Optional, Tuple, Dict, Any
# We assume 'firebase_admin' is installed via pip (handled by the Dockerfile)
import firebase_admin
from firebase_admin import auth, credentials
from synapse.module_api import ModuleApi
from synapse.api.errors import SynapseError

logger = logging.getLogger(__name__)

class FirebaseAuthProvider:
    def __init__(self, config: Dict[str, Any], api: ModuleApi):
        # Store the API object for provisioning later
        self.api = api
        self.config = config
        self.server_name = api.server_name  # Get Synapse's configured server name

        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            # Check if credentials path is provided in config
            creds_path = config.get("firebase_credentials_path")
            if creds_path:
                # Initialize with service account credentials
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account credentials")
            else:
                # Initialize with default credentials (useful for GCP environments)
                firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized with default credentials")
        else:
            logger.info("Firebase Admin SDK already initialized")

        api.register_password_auth_provider_callbacks(
            auth_checkers={
                ("m.login.firebase", ("token",)): self.verify_firebase_token,
            },
        )


    async def verify_firebase_token(
            self, username: str, login_type: str, login_dict: Dict[str, Any]
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Synapse calls this method to authenticate the user using a custom login flow.
        """
        # 1. --- Input Validation (Match the custom login type) ---
        # Assuming you defined a custom login type for Firebase token submission
        # if login_type != "m.login.firebase":
        #     return None  # Not our login type, let other providers handle it

        firebase_token = login_dict.get("token")
        if not firebase_token:
            return None

        try:
            # 2. --- Verify Token (External Call to Firebase) ---
            # This is the line that communicates securely with Firebase's servers
            decoded_token = auth.verify_id_token(firebase_token)

            # Extract the unique Firebase User ID (UID)
            firebase_uid = decoded_token.get("uid")
            display_name = decoded_token.get("name") or firebase_uid

            # 3. --- Map to Matrix ID ---
            # The Synapse localpart is based on the Firebase UID
            localpart = firebase_uid
            matrix_id = f"@{localpart}:{self.server_name}"
            logger.info(f"Firebase UID: {firebase_uid}")
            logger.info(f"display name: {display_name}")
            logger.info(f"matrix_id: {matrix_id}")

            # 4. --- Provision User (Synapse Registration Check) ---

            # Check if the user already exists in the Synapse database
            user_id_obj = self.api.get_qualified_user_id(localpart)
            logger.warning(f"obj id is: {user_id_obj}")
            user_exists = await self.api.check_user_exists(user_id_obj)
            logger.warning(f"user exists is: {user_exists}")

            if not user_exists:
                logger.info(f"Firebase user {localpart} does not exist in Synapse. Provisioning...")

                # Provision the user account using the Module API
                await self.api.register_user(
                    localpart=localpart,
                    displayname=display_name,
                )
                logger.info(f"User {matrix_id} successfully provisioned.")

            # 5. --- Final Return ---
            # Authentication is successful. Return the canonical Matrix ID.
            return matrix_id, None

        except auth.InvalidIdTokenError:
            # Token is expired, invalid, or improperly formatted
            logger.warning("Invalid or expired Firebase ID token provided.")
            return None
        except SynapseError as e:
            logger.error(f"Synapse Error during provisioning: {e}")
            return None
        except Exception as e:
            logger.error(f"Unknown Firebase Auth error: {e}")
            return None
