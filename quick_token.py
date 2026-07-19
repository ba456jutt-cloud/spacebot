import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

def main():
    if os.path.exists("token.json"):
        os.remove("token.json")
        
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    print("✅ SUCCESS! token.json has been generated successfully.")

if __name__ == "__main__":
    main()
