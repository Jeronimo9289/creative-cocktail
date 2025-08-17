# ================================
# app/frontend/forms.py
# ================================

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField, DecimalField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from wtforms.widgets import TextArea
from app.models.user import UserType
from app.models.event import EventType

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Prénom', validators=[DataRequired()])
    last_name = StringField('Nom', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirmer le mot de passe', 
                             validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('Type de compte', 
                          choices=[(UserType.CLIENT.value, 'Client'), 
                                  (UserType.PROVIDER.value, 'Prestataire')],
                          default=UserType.CLIENT.value)
    
    def validate_username(self, username):
        from app.models.user import User
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    
    def validate_email(self, email):
        from app.models.user import User
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Cette adresse email est déjà utilisée.')

class EventForm(FlaskForm):
    title = StringField('Titre de l\'événement', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    event_type = SelectField('Type d\'événement',
                            choices=[(EventType.PERSONAL.value, 'Particulier'),
                                   (EventType.PROFESSIONAL.value, 'Professionnel')],
                            validators=[DataRequired()])
    total_budget = DecimalField('Budget total (€)', validators=[Optional(), NumberRange(min=0)])
    expected_participants = IntegerField('Nombre de participants attendus', 
                                       validators=[Optional(), NumberRange(min=1)])
    start_date = DateTimeField('Date de début', validators=[Optional()])
    end_date = DateTimeField('Date de fin', validators=[Optional()])

class VenueForm(FlaskForm):
    name = StringField('Nom du lieu', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    address = TextAreaField('Adresse', validators=[DataRequired()])
    postal_code = StringField('Code postal', validators=[Length(max=10)])
    city = StringField('Ville', validators=[DataRequired(), Length(max=100)])
    country = StringField('Pays', validators=[Length(max=100)])
    max_capacity = IntegerField('Capacité maximale', validators=[Optional(), NumberRange(min=1)])
    min_capacity = IntegerField('Capacité minimale', validators=[Optional(), NumberRange(min=1)])
    base_price = DecimalField('Prix de base (€)', validators=[Optional(), NumberRange(min=0)])
    contact_person = StringField('Personne de contact', validators=[Length(max=100)])
    phone = StringField('Téléphone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    website = StringField('Site web', validators=[Length(max=200)])