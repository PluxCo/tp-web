import datetime

from wtforms.fields import StringField, SelectMultipleField, IntegerField, TimeField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from wtforms.widgets import TextInput

from ._ext import BasePrefixedForm

from tools import WeekDays


class TimeDeltaField(StringField):
    def _value(self):
        if self.data:
            return self.dump_time_delta(self.data)
        return ""

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = self.parse_time_delta(valuelist[0])
        else:
            self.data = datetime.timedelta()

    @staticmethod
    def parse_time_delta(time_delta_str: str):
        dr = {'d': 0, 'h': 0, 'm': 0, 's': 0}
        prev_num = ""
        for s in time_delta_str:
            if s in dr:
                dr[s] = int(prev_num)
                prev_num = ""
            elif s.isdigit():
                prev_num += s
        if len(prev_num):
            dr['s'] = int(prev_num)
        return datetime.timedelta(days=dr['d'], hours=dr['h'], minutes=dr['m'], seconds=dr['s'])

    @staticmethod
    def dump_time_delta(delta: datetime.timedelta):
        res = str(delta.days) + 'd' if delta.days else ""
        seconds = delta.seconds
        res += str(seconds // 3600) + 'h' if seconds // 3600 else ""
        seconds %= 3600
        res += str(seconds // 60) + 'm' if seconds // 60 else ""
        seconds %= 60
        res += str(seconds) + 's' if seconds else ""
        return res


class TelegramSettingsForm(BasePrefixedForm):
    tg_pin = StringField("Telegram auth pin")

    save_tg = SubmitField("Save")


class ScheduleSettingsForm(BasePrefixedForm):
    time_period = TimeDeltaField("Period", validators=[DataRequired()])
    week_days = SelectMultipleField("Week days", choices=[(WeekDays.Monday.value, "Monday"),
                                                          (WeekDays.Tuesday.value, "Tuesday"),
                                                          (WeekDays.Wednesday.value, "Wednesday"),
                                                          (WeekDays.Thursday.value, "Thursday"),
                                                          (WeekDays.Friday.value, "Friday"),
                                                          (WeekDays.Saturday.value, "Saturday"),
                                                          (WeekDays.Sunday.value, "Sunday")],
                                    coerce=int)
    from_time = TimeField("From", validators=[DataRequired()])
    to_time = TimeField("To", validators=[DataRequired()])

    save_schedule = SubmitField("Save")

    def validate_time_period(self, field):
        if field.data.total_seconds() < 30:
            raise ValidationError("Time delta should be at least 30 seconds")


class SessionSettingsForm(BasePrefixedForm):
    max_time = TimeDeltaField("Session time", validators=[DataRequired()])
    max_questions = IntegerField("Questions in the session", validators=[DataRequired()])

    save_session_settings = SubmitField("Save")
