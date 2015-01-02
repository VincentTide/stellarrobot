from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo


class RobotForm(Form):
    name_or_address = StringField('Name')
    submit = SubmitField('Submit')
