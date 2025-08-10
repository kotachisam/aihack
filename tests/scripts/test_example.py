def hello_world() -> None:
    print("Hello, World!")


def add_numbers(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    hello_world()
    result = add_numbers(5, 3)
    print(f"5 + 3 = {result}")
