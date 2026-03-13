"""One-time script to generate OAuth2 token for Gmail and Calendar access.

Run this once: python generate_token.py
It opens a browser window for Google sign-in and saves token.json.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

from auth import SCOPES


def main():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as f:
        f.write(creds.to_json())

    print("Token saved to token.json")
    print(f"Scopes granted: {creds.scopes}")


if __name__ == "__main__":
    main()
