# 📊 Veritabanı Bağlantısı (SQLite)

Bu projede, kullanıcı bilgileri ve çalışma planları **SQLite** veritabanı kullanılarak saklanmaktadır.  
Aşağıda, projede kullanılan veritabanı bağlantısı ve işlemlerine dair örnek kodlar yer almaktadır.

---

## 1. Veritabanı Bağlantısı

Aşağıdaki fonksiyon, `veritabani.db` dosyasına bağlantı kurar:

```python
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('veritabani.db')  # Veritabanına bağlantı
    conn.row_factory = sqlite3.Row
    return conn
```

---

## 2. Kullanıcı Tablosunun Oluşturulması

Uygulama ilk kez çalıştığında, kullanıcı bilgilerini tutmak için `users` tablosu oluşturulur:

```python
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
```

---

## 3. Kullanıcı Doğrulama İşlemi

Kullanıcının var olup olmadığını kontrol eden fonksiyon:

```python
def check_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user
```

---

## 4. Özet

- Kullanıcı bilgileri SQLite veritabanında saklanır (`veritabani.db`)
- SQL komutları doğrudan Python içerisinde yazılmıştır
- Kodlar `sqlite3` kütüphanesi ile çalışmaktadır

> Bu dosya, projenin SQL veritabanı ile aktif olarak çalıştığını kanıtlar niteliktedir ✅