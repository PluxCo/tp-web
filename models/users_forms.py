from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    passwd = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    passwd = PasswordField("Password", validators=[DataRequired()])
    repasswd = PasswordField("Repeat password", validators=[DataRequired()])
