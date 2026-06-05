import requests

def fetch_user_profile(user_id):
    response = requests.request(
        'GET',
        f'https://api.example.com/users/{user_id}'
    )
    return response.json()
