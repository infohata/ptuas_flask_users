from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField
from wtforms.validators import DataRequired, ValidationError, EqualTo
import app


class RegistracijosForma(FlaskForm):
    vardas = StringField('Vardas', [DataRequired()])
    el_pastas = StringField('El. paštas', [DataRequired()])
    slaptazodis = PasswordField('Slaptažodis', [DataRequired()])
    patvirtintas_slaptazodis = PasswordField("Pakartokite slaptažodį", [EqualTo('slaptazodis', "Slaptažodis turi sutapti.")])
    submit = SubmitField('Prisiregistruoti')

    def validate_vardas(self, vardas):
        with app.app.app_context():
            vartotojas = app.Vartotojas.query.filter_by(
                vardas=vardas.data).first()
            if vartotojas:
                raise ValidationError(
                    'Šis el. pašto adresas panaudotas. Pasirinkite kitą.')

    def validate_el_pastas(self, el_pastas):
        with app.app.app_context():
            vartotojas = app.Vartotojas.query.filter_by(
                el_pastas=el_pastas.data).first()
            print(vartotojas)
            if vartotojas:
                raise ValidationError(
                    'Šis vardas panaudotas. Pasirinkite kitą.')

