from flask import Flask, render_template, request, redirect, url_for, session, jsonify  # type: ignore
import bcrypt  # type: ignore
from flask_cors import CORS  # type: ignore

app = Flask(__name__)
CORS(app)
app.secret_key = 'somerandomsecretkey'

# Derslerin zorluk derecesine göre önerilen süreler (saat cinsinden)
DERS_SURELERI = {
    "Matematik": 3,
    "Fizik": 2.5,
    "Kimya": 2,
    "Biyoloji": 2,
    "Edebiyat": 1.5,
    "Tarih": 1.5
}

# Derslere özel çalışma yöntemleri
CALISMA_YONTEMLERI = {
    "Matematik": "Bol bol soru çöz ve zaman tutarak deneme yap.",
    "Fizik": "Formülleri kavrayarak öğren ve deney videoları izle.",
    "Kimya": "Konu özetleri çıkar, ezber yerine mantığını anla.",
    "Biyoloji": "Şemalar ve görsellerle çalış, sesli tekrar yap.",
    "Edebiyat": "Önemli yazarları, eserleri not alarak tekrar et.",
    "Tarih": "Kronolojik sıralama yaparak, haritalarla öğren."
}

# Kullanıcılar hafızada tutulacak
users_db = {}

# Kullanıcı ekleme fonksiyonu
def add_user_to_db(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_db[username] = {
        'password': hashed_password,
        'tasks': []
    }

# Kullanıcı adı daha önce var mı kontrol et
def check_username_exists(username):
    return username in users_db

def check_user(username, password):
    if username in users_db:
        user = users_db[username]
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return user
    return None

# Kullanıcıya ait görevleri getir
def get_user_tasks(user_id):
    return users_db.get(user_id, {}).get('tasks', [])

# Görev ekleme
def add_task_to_db(user_id, task):
    if user_id in users_db:
        users_db[user_id]['tasks'].append(task)

# Ana sayfa yönlendirmesi (Giriş kontrolü)
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# Kayıt olma sayfası
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_username_exists(username):
            return 'Bu kullanıcı adı zaten mevcut', 400
        add_user_to_db(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

# Giriş yapma sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Kullanıcı adı veya şifre yanlış', 403
    return render_template('login.html')

# Kullanıcı giriş yaptıktan sonra yönlendirilecek sayfa
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        username = session['username']
        tasks = get_user_tasks(username)
        if request.method == 'POST':
            task = request.form['task']
            add_task_to_db(username, task)
            return redirect(url_for('index'))
        return render_template('index.html', username=username, tasks=tasks)
    return redirect(url_for('login'))

# Çıkış işlemi
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Çalışma önerisi endpoint (JSON ile)
@app.route('/calisma-onerisi', methods=['POST'])
def calisma_onerisi():
    data = request.get_json()
    ad = data.get("ad", "Bilinmiyor")
    ders = data.get("ders", "Genel")
    konular = data.get("konular", [])
    calisma_saatleri = data.get("calisma_saatleri", [])

    yanit = {"ad": ad, "oneriler": []}

    # Ders için belirlenen çalışma süresini kullan
    max_saat = DERS_SURELERI.get(ders, 2)  # Varsayılan: 2 saat
    calisma_yontemi = CALISMA_YONTEMLERI.get(ders, "Bu ders için özel bir öneri bulunmamaktadır.")

    for konu in konular:
        if calisma_saatleri:
            available_hour = calisma_saatleri.pop(0)  # İlk boş saat aralığını al
            yanit["oneriler"].append({
                "konu": konu,
                "sure": max_saat,
                "yontem": calisma_yontemi,
                "zaman": available_hour  # Kullanıcının belirlediği saat
            })
        else:
            yanit["oneriler"].append({
                "konu": konu,
                "sure": max_saat,
                "yontem": calisma_yontemi,
                "zaman": "Kendi belirlediğiniz bir saat"
            })

    return jsonify(yanit)

# Flask uygulamasını çalıştır
if __name__ == "__main__":
    app.run(debug=True)
