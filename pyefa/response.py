class EfaResponse:
    def __init__(self, raw_data: str) -> None:
        self._raw = raw_data

        print(raw_data)

    def parse(self):
        return "Hello"
