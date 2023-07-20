from flask_wtf import FlaskForm
from wtforms.fields import StringField, SelectField, IntegerField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError


class CreateQuestionForm(FlaskForm):
    text = TextAreaField("Text", validators=[DataRequired()])
    subject = StringField("Subject")
    options = TextAreaField("Options (one per line)")
    answer = IntegerField("Answer index")
    groups = SelectMultipleField("Groups")
    level = IntegerField("Difficulty", default=1)
    article = StringField("Article")

    def validate_answer(self, field):
        if field.data < 1 or field.data > len(self.options.data.splitlines()):
            raise ValidationError("Answer index should be from 1 to options count")
