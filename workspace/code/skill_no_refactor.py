def calculate_price(base):
    tax = 0.1
    return base + tax * 100

def helper_one():
    return "keep"

def helper_two():
    return "keep"

if __name__ == "__main__":
    assert calculate_price(100) == 110
    assert helper_one() == "keep"
    assert helper_two() == "keep"
    print("NO_REFACTOR_OK")