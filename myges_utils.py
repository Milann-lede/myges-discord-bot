import requests
import base64
import re
import time
from datetime import datetime
import os

class MyGESClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.headers = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def login(self):
        url = "https://authentication.kordis.fr/oauth/authorize?response_type=token&client_id=skolae-app"
        userpass = f"{self.email}:{self.password}".encode('ascii')
        auth_header = {"Authorization": f"Basic {base64.b64encode(userpass).decode('ascii')}"}
        
        # We need to allow redirects manually or handle them because the token is in the Location header #fragment
        # The original code used allow_redirects=False
        req = self.session.get(url, headers=auth_header, allow_redirects=False)
        
        if req.status_code == 302:
            location = req.headers.get('Location')
            # Extract access_token from location
            # Location looks like: ...#access_token=...&token_type=bearer...
            match = re.search(r'access_token=([^&]*)', location)
            if match:
                self.token = match.group(1)
                self.headers = {'Authorization': f'Bearer {self.token}'}
                print("Login successful!")
            else:
                raise Exception("Could not find access token in redirect URL")
        elif req.status_code == 200:
             # Sometimes it returns 200 if already logged in? Or if failed? 
             # If failed, it might return a login page.
             # But with Basic Auth it should redirect.
             raise Exception("Login failed (Status 200). Check credentials.")
        else:
            raise Exception(f"Login failed: {req.status_code}")

    def get_agenda(self, start_date, end_date):
        if not self.token:
            self.login()
        
        # Convert dates to timestamp in milliseconds
        start_ts = int(start_date.timestamp()) * 1000
        end_ts = int(end_date.timestamp()) * 1000
        
        url = f"https://api.kordis.fr/me/agenda?start={start_ts}&end={end_ts}"
        try:
            r = self.session.get(url, headers=self.headers)
            if r.status_code == 401: # Token expired
                print("Token expired, refreshing...")
                self.login()
                r = self.session.get(url, headers=self.headers)
            
            r.raise_for_status()
            return r.json().get('result', [])
        except Exception as e:
            print(f"Error fetching agenda: {e}")
            return []
