def login_user(username, password):
    token = authenticate(username, password)
    return token

def authenticate(user, pwd):
    return 'fake_token'
