import os
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, logout_user, login_user, UserMixin, login_required
import secrets
from PIL import Image
import forms
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'manobataibuvodu1dingo3turiu'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'vartotojai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "prisijungti"


class Vartotojas(db.Model, UserMixin):
    __tablename__ = "vartotojas"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String(20), unique=True, nullable=False)
    el_pastas = db.Column("El. pašto adresas", db.String(120), unique=True, nullable=False)
    slaptazodis = db.Column("Slaptažodis", db.String(60), nullable=False)
    nuotrauka = db.Column("Nuotrauka", db.String(200), nullable=False, default='default.png')

    def __repr__(self):
        return str(self.vardas)


class Irasas(db.Model):
    __tablename__ = "irasas"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column("Data", db.DateTime)
    irasas = db.Column("irasas", db.Text)
    vartotojas_id = db.Column(db.Integer, db.ForeignKey("vartotojas.id"))
    vartotojas = db.relationship("Vartotojas", backref="irasai")


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(vartotojo_id):
    return Vartotojas.query.get(int(vartotojo_id))

class UserModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.el_pastas == "kestas@midonow.fi"
    
class IrasasAdminView(UserModelView):
    column_filters = ['vartotojas_id']
    form_ajax_refs = {
        'vartotojas': {
            'fields': ['vardas', 'el_pastas'],
            'page_size': 10
        }
    }

admin = Admin(app)
admin.add_view(IrasasAdminView(Irasas, db.session))
admin.add_view(UserModelView(Vartotojas, db.session))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registruotis", methods=['GET', 'POST'])
def registruotis():
    # db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegistracijosForma()
    if form.validate_on_submit():
        koduotas_slaptazodis = bcrypt.generate_password_hash(
            form.slaptazodis.data
        ).decode('utf-8')
        vartotojas = Vartotojas(
            vardas=form.vardas.data, 
            el_pastas=form.el_pastas.data, 
            slaptazodis=koduotas_slaptazodis
        )
        db.session.add(vartotojas)
        db.session.commit()
        flash('Sėkmingai prisiregistravote! Galite prisijungti', 'success')
        return redirect(url_for('index'))
    return render_template('registruotis.html', title='Register', form=form)

def save_picture(form_picture):
    belenkas = secrets.token_hex(8)
    _, failo_galune = os.path.splitext(form_picture.filename)
    nuotraukos_failo_pavadinimas = belenkas + failo_galune
    picture_path = os.path.join(app.root_path, 'static/profilio_nuotraukos', nuotraukos_failo_pavadinimas)
    output_size = (300, 300)
    nuotrauka = Image.open(form_picture)
    nuotrauka.thumbnail(output_size)
    nuotrauka.save(picture_path)
    return nuotraukos_failo_pavadinimas

@app.route("/paskyra", methods=['GET', 'POST'])
@login_required
def account():
    form = forms.PaskyrosAtnaujinimoForma()
    if form.validate_on_submit():
        if form.nuotrauka.data:
            if current_user.nuotrauka != "default.png":
                senos_nuotraukos_failas = os.path.join(app.root_path, 'static/profilio_nuotraukos', current_user.nuotrauka)
                os.remove(senos_nuotraukos_failas)
            nuotrauka = save_picture(form.nuotrauka.data)
            current_user.nuotrauka = nuotrauka
        current_user.vardas = form.vardas.data
        current_user.el_pastas = form.el_pastas.data
        db.session.commit()
        flash('Tavo paskyra atnaujinta!', 'success')
        return redirect(url_for('account'))
    form.vardas.data = current_user.vardas
    form.el_pastas.data = current_user.el_pastas
    nuotrauka = url_for(
        'static', filename='profilio_nuotraukos/' + current_user.nuotrauka)
    return render_template('paskyra.html', title='Account', form=form, nuotrauka=nuotrauka)

@app.route("/prisijungti", methods=['GET', 'POST'])
def prisijungti():
    if current_user.is_authenticated:
        flash('Jūs vis dar esate prisijungęs', 'warning')
        return redirect(url_for('index'))
    form = forms.PrisijungimoForma()
    if form.validate_on_submit():
        user = Vartotojas.query.filter_by(
            el_pastas=form.el_pastas.data
        ).first()
        if user and bcrypt.check_password_hash(user.slaptazodis, form.slaptazodis.data):
            login_user(user, remember=form.prisiminti.data)
            # next_page = request.args.get('next')
            # return redirect(next_page) if next_page else redirect(url_for('index'))
            flash(f'Sveiki {user.vardas} sėkmingai prisijungę!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Prisijungti nepavyko. Patikrinkite el. paštą ir slaptažodį', 'danger')
    return render_template('prisijungti.html', title='Prisijungti', form=form)

@app.route("/atsijungti")
def atsijungti():
    logout_user()
    flash('Viso gero!', 'secondary')
    return redirect(url_for('index'))

@app.route("/irasai")
@login_required
def records():
    page = request.args.get('page', 1, type=int)
    visi_irasai = Irasas.query.filter_by(vartotojas_id=current_user.id).order_by(
        Irasas.data.desc()).paginate(page=page, per_page=3)
    return render_template("irasai.html", visi_irasai=visi_irasai, datetime=datetime)

@app.route("/naujas_irasas", methods=["GET", "POST"])
def new_record():
    form = forms.IrasasForm()
    if form.validate_on_submit():
        naujas_irasas = Irasas(irasas=form.irasas.data, vartotojas_id=current_user.id, data=datetime.now())
        db.session.add(naujas_irasas)
        db.session.commit()
        flash(f"Įrašas sukurtas", 'success')
        return redirect(url_for('records'))
    return render_template("prideti_irasa.html", form=form)

if __name__ == "__main__":
    app.run()
