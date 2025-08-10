def login(username, password):
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (
        username,
        password,
    )
    return query


def process_input():
    user_input = input("Enter command: ")
    result = eval(user_input)
    return result


# Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"


def read_file(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()
