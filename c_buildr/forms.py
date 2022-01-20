from flask_wtf import Form
from wtforms import StringField, PasswordField, TextField
from wtforms.validators import DataRequired, Email


class EmailForm(Form):
    email = StringField("Email", validators=[DataRequired(), Email()])


class PasswordForm(Form):
    password = PasswordField("Email", validators=[DataRequired()])
