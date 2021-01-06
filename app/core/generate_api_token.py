import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']
PATH = './token/token.pkl'


def generate_creds():
    creds = None
    if os.path.exists(PATH):
        with open(PATH, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed":
                    {
                        "project_id": input('PROJECT_ID: '),
                        "client_id": input('CLIENT_ID: '),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": input('CLIENT_SECRET: '),
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(PATH, 'wb') as token:
            pickle.dump(creds, token)
    return creds


if __name__ == '__main__':
    generate_creds()
    print("Your token was generated successfully!")
