from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length , ValidationError
from models import Department
from database import get_session

def get_department_choices():
    session = get_session()
    departments = session.query(Department).all()
    choices = [(dept.department_id, dept.department_name) for dept in departments]
    session.close()
    return choices

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    department = SelectField('Department', choices=get_department_choices(), validators=[DataRequired()])
    submit = SubmitField('Register')
    def validate_email(self, email):
        if not email.data.endswith('@nucleusteq.com'):
            raise ValidationError('Enter valid email')
        
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    submit = SubmitField('Login')
    
    def validate_email(self, field):
        if not field.data.endswith('@nucleusteq.com'):
            raise ValidationError('Enter Valid Email.')

class ReimbursementForm(FlaskForm):
    date = DateField('Date of Expense', format='%Y-%m-%d', validators=[DataRequired()])
    expense_type = SelectField('Expense Type', choices=[('Travel', 'Travel'), ('Accommodation', 'Accommodation'), ('Food', 'Food'), ('Other', 'Other')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    document = StringField('Document Path', validators=[DataRequired()])  # This can be updated to handle file uploads
    submit = SubmitField('Submit Reimbursement Request')
