import os
import sys
import json
import logging

# Ensure project root is in sys.path
sys.path.append(os.path.join(os.getcwd(), "functions", "smart_railway_app_function"))

from functions.smart_railway_app_function.main import create_flask_app
from functions.smart_railway_app_function.routes.session_auth import employee_login

logging.basicConfig(level=logging.INFO)

app = create_flask_app()

def test_login():
    with app.test_request_context(
        method='POST',
        json={'email': 'testhari20@gmail.com', 'password': 'Password@123'},
        headers={'Content-Type': 'application/json'}
    ):
        try:
            response = employee_login()
            if hasattr(response, 'get_json'):
                print(json.dumps(response.get_json(), indent=2))
            else:
                # Flask can return a tuple or direct response
                print(response)
        except Exception as e:
            print(f"Error during login: {e}")

if __name__ == "__main__":
    test_login()
