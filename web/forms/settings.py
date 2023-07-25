from flask_wtf import FlaskForm
from wtforms.fields import StringField, SelectMultipleField, IntegerField, TimeField
from wtforms.validators import DataRequired
from schedule import WeekDays


class TelegramSettingsForm(FlaskForm):
    tg_pin = StringField("Telegram auth pin")


class ScheduleSettingsForm(FlaskForm):
    time_period = StringField("Period")
    week_days = SelectMultipleField("Week days", choices=[(WeekDays.Monday, "Monday"),
                                                          (WeekDays.Tuesday, "Tuesday"),
                                                          (WeekDays.Wednesday, "Wednesday"),
                                                          (WeekDays.Thursday, "Thursday"),
                                                          (WeekDays.Friday, "Friday"),
                                                          (WeekDays.Saturday, "Saturday"),
                                                          (WeekDays.Sunday, "Sunday"), ])
    from_time = TimeField("From")
    to_time = TimeField("To")
