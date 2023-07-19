from flask_wtf import FlaskForm
from sqlalchemy import exists
from wtforms.fields import PasswordField, StringField
from wtforms.validators import DataRequired, ValidationError

from models import db_session, users


class LoginForm(FlaskForm):
    passwd = PasswordField("Password", validators=[DataRequired()])


class CreateGroupForm(FlaskForm):
    name = StringField("Label", validators=[DataRequired()])

    def validate_name(self, field):
        db = db_session.create_session()
        if db.query(exists().where(users.PersonGroup.name == self.name.data)).scalar():
            raise ValidationError("This group already exists")


class UserCork:
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def get_id(self):
        return 1
