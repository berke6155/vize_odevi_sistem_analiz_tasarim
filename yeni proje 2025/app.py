import re
import os
import bcrypt
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = 'somerandomsecretkey'

# Veritabanı dosyasının yolu
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "database.db")

# Flask için SQLite bağlantısını ayarla
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Kullanıcı Modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Görev Modeli
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task = db.Column(db.String(255), nullable=False)

# Çalışma Planı Modeli
class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    study_hours = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user = db.relationship('User', backref=db.backref('study_plans', lazy=True))

with app.app_context():
    db.create_all()

# Şifre güvenlik kriterlerini kontrol eden fonksiyon
def is_password_valid(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;"\'<>,.?\/\\\-]).{8,}$'
    return re.match(pattern, password)

def add_user_to_db(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

def check_username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def check_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return user
    return None

# API ile ders önerilerini almak için fonksiyon
def get_ders_onerisi(subject):
    api_key = os.getenv("GEMINI_API_KEY")
    # Gerçek API URL'sini buraya yazın (örneğin, gemini API endpoint'iniz)
    url = f"https://gemini.api.com/recommendations?subject={subject}&api_key={api_key}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()  # API'den gelen önerileri döndür
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"API çağrısında hata: {e}")
        return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        flash('Zaten giriş yapmışsınız.', 'info')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not is_password_valid(password):
            flash('Şifre en az 8 karakter uzunluğunda, bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir.', 'error')
            return redirect(url_for('register'))
        if check_username_exists(username):
            flash('Bu kullanıcı adı zaten mevcut', 'error')
            return redirect(url_for('register'))
        add_user_to_db(username, password)
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        flash('Zaten giriş yapmışsınız.', 'info')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)
        if user:
            session['username'] = username
            session['user_id'] = user.id
            flash('Başarıyla giriş yaptınız', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Kullanıcı adı veya şifre yanlış', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
@app.route('/index')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Lütfen önce giriş yapın.', 'warning')
        return redirect(url_for('login'))
    user_id = session['user_id']
    study_plans = StudyPlan.query.filter_by(user_id=user_id).all()
    # Her plan için, API'den ders önerisini alıp geçici olarak ekliyoruz.
    for plan in study_plans:
        rec = get_ders_onerisi(plan.subject)
        if rec and "suggestions" in rec:
            plan.recommendation = rec["suggestions"]
        else:
            plan.recommendation = "Öneri bilgisi bulunamadı."
    return render_template('dashboard.html', username=session['username'], study_plans=study_plans)

@app.route('/create_plan', methods=['POST'])
def create_plan():
    if 'username' not in session:
        flash('Lütfen önce giriş yapın.', 'warning')
        return redirect(url_for('login'))
    subject = request.form.get("subject")
    topic = request.form.get("topic")
    study_hours = request.form.get("study_hours")
    if not subject or not topic or not study_hours:
        flash("Tüm alanları doldurun!", "error")
        return redirect(url_for('dashboard'))
    try:
        study_hours = float(study_hours)
    except ValueError:
        flash("Çalışma saatleri sayı olmalıdır!", "error")
        return redirect(url_for('dashboard'))
    user_id = session['user_id']
    new_plan = StudyPlan(
        user_id=user_id,
        subject=subject,
        topic=topic,
        study_hours=study_hours
    )
    db.session.add(new_plan)
    db.session.commit()
    flash("Çalışma planınız kaydedildi!", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete_plan/<int:plan_id>', methods=['POST'])
def delete_plan(plan_id):
    if 'username' not in session:
        flash("Lütfen önce giriş yapın.", "warning")
        return redirect(url_for('login'))
    plan = StudyPlan.query.get(plan_id)
    if plan and plan.user_id == session['user_id']:
        db.session.delete(plan)
        db.session.commit()
        flash("Plan silindi.", "success")
    else:
        flash("Plan silinemedi.", "error")
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True, port=8000)
