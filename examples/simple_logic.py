# examples/simple_logic.py
# type: ignore  # This file contains intentional issues for AI analysis

import os


def get_user_data(user_id: int) -> dict | None:
    """Fetches user data from a mock source."""
    # In a real app, this would fetch from a database
    if user_id == 1:
        return {"name": "Alice", "email": "alice@example.com"}
    return None


def process_file(filename: str) -> None:
    """Reads data from a file and prints its length."""
    # This is an insecure way to open files!
    data = open(filename, "r").read()
    print(f"Processing {len(data)} bytes from {filename}")


if __name__ == "__main__":
    user = get_user_data(1)
    print(f"User found: {user['name']}")

    # Create a dummy file to process
    dummy_file = "temp_data.txt"
    with open(dummy_file, "w") as f:
        f.write("hello world")

    process_file(dummy_file)

    os.remove(dummy_file)
