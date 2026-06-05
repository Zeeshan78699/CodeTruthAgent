def save_user_data(data):
    with open('out.txt', 'w') as f:
        f.write(data)
    return True
