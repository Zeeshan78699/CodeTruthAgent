class Parser:
    def parse(self, d: str): return {}
    def validate(self, d): return True

class JsonParser(Parser):
    def parse(self, d: str): return {}

class XmlParser(Parser):
    def parse(self, d: str): return {}

def create_parser(fmt: str) -> Parser:
    if fmt == 'json':
        return JsonParser()
    return XmlParser()

def process(fmt: str, raw: str):
    parser = create_parser(fmt)
    r = parser.parse(raw)
    v = parser.validate(r)
    return r
