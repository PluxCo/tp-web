from flask_wtf import FlaskForm
from wtforms.fields import StringField, SelectField, IntegerField
from wtforms.validators import DataRequired


class SettingsForm(FlaskForm):
    protection_type = SelectField("Protection type",
                                  choices=[("none", "None"),
                                           ("single", "Select digit"),
                                           ("single_random", "Select random digit"),
                                           ("text", "Type text"),
                                           ("random_num", "Type random number")])
    protection_key = StringField("Protection key")

    bot_timeout = IntegerField("Bot timeout (s)")
