from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    passwd = PasswordField("Password", validators=[DataRequired()])


class UserCork:
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return 1
