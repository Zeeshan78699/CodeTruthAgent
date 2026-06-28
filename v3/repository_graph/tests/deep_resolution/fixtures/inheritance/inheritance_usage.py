class BaseValidator:
    def validate(self, v): return True
    def get_errors(self): return []
    def reset(self): pass

class StringValidator(BaseValidator):
    def validate(self, v: str) -> bool:
        return isinstance(v, str)

class FormValidator(StringValidator):
    def validate_form(self, form: dict) -> bool:
        for k, v in form.items():
            if not self.validate(str(v)):
                return False
        e = self.get_errors()
        self.reset()
        return len(e) == 0

def run(data: dict):
    fv = FormValidator()
    r = fv.validate_form(data)
    e = fv.get_errors()
    fv.reset()
    return r, e
