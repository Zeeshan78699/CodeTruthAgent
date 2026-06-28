class Config:
    def __init__(self):
        self._host = 'localhost'
        self._port = 5432

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

class App:
    def __init__(self):
        self.config = Config()

    def connect(self):
        h = self.config.host
        p = self.config.port
        return f'{h}:{p}'
