from .example_reader import ExampleReader

def get_reader_for_bank(bank_code):
    mapping = {
        "EXAMPLE": ExampleReader()
    }
    return mapping.get(bank_code.upper(), ExampleReader())
