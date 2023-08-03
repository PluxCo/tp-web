from flask_wtf import FlaskForm
from sqlalchemy import exists
from wtforms import SubmitField
from wtforms.fields import PasswordField, StringField
from wtforms.validators import DataRequired, ValidationError

from ._ext import BasePrefixedForm

from models import db_session, users


class LoginForm(BasePrefixedForm):
    passwd = PasswordField("Password", validators=[DataRequired()])


class CreateGroupForm(BasePrefixedForm):
    name = StringField("Label", validators=[DataRequired()])

    create_group = SubmitField("Create")

    def validate_name(self, field):
        db = db_session.create_session()
        if db.query(exists().where(users.PersonGroup.name == self.name.data)).scalar():
            raise ValidationError("This group already exists")


class PausePersonForm(BasePrefixedForm):
    pause = SubmitField("Pause")
    unpause = SubmitField("Unpause")


class UserCork:
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return 1
