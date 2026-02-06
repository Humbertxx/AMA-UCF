from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, Length


class RegistrationForm(FlaskForm):
    calendar_name = StringField('calendar_name',default='AMA Calendar', validators=[DataRequired(), Length(min =10, max =20)])
    calendar_timezone = StringField('timezone', default='America/New_York', filters=[lambda x: x.strip() if x else x])
    worksheet_id = StringField('worksheet_id', default='')
    access_code = PasswordField('access_code', validators=[DataRequired()])
    secret_dir = FileField('secret_dir', validators=[DataRequired()])
    target_calendar_id = FileField('target_calendar_id', validators=[DataRequired()])

    submit = SubmitField('Setting are Ready')
