import requests
import json
from app.core.config import AppConfig
from logging import Logger


def get_refresh_token(config: AppConfig, logger: Logger) -> str:
    payload = {
        "mailaddress": config.jquants.auth.email,
        "password": config.jquants.auth.password
    }

    try:
        response = requests.post(config.jquants.endpoints.token_auth_user, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        refresh_token = data["refreshToken"]
        logger.info("Successfully obtained refresh token.")
        return refresh_token
    except requests.HTTPError as e:
        logger.error(f"HTTP error occurred during refresh token request: {e} - {response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred during refresh token request: {e}")
        raise

def get_id_token(config: AppConfig, refresh_token: str, logger: Logger) -> str:
    try:
        url = f"{config.jquants.endpoints.token_auth_refresh}?refreshtoken={refresh_token}"
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()
        id_token = data["idToken"]
        logger.info("Successfully obtained ID token.")
        return id_token
    except requests.HTTPError as e:
        logger.error(f"HTTP error occurred during ID token request: {e} - {response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred during ID token request: {e}")
        raise
