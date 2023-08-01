from flask_wtf import FlaskForm
from flask_wtf.form import _Auto


class BasePrefixedForm(FlaskForm):
    def __init__(self, form_data=_Auto, **kwargs):
        if "prefix" not in kwargs:
            super().__init__(form_data, prefix=type(self).__name__, **kwargs)
        else:
            super().__init__(form_data, **kwargs)
