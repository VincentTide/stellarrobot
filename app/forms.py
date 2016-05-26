from flask.ext.wtf import Form
from wtforms import StringField, SubmitField


class RobotForm(Form):
    name_or_address = StringField('Name')
    submit = SubmitField('Submit')
