def process_data(data):
    results = []
    for item in data:
        if item != None:
            results.append(item * 2)
    return results


def divide_numbers(a: float, b: float) -> float:
    return a / b


class DataProcessor:
    def __init__(self) -> None:
        self.data: List[Any] = []

    def add_data(self, item: Any) -> None:
        self.data.append(item)

    def process_all(self) -> List[Any]:
        return [x * 3 for x in self.data if x > 0]


# Some potential issues for AI to find:
# - No type hints
# - No error handling in divide_numbers (division by zero)
# - Using `item != None` instead of `item is not None`
# - No docstrings
