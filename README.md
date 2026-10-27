# 🔒 LocalPW Maker - Güvenli Yerel Şifre Yöneticisi

**LocalPW Maker**, kullanıcı verilerinin gizliliğini ve donanım bazlı güvenliği ön planda tutan, tamamen yerel (offline) çalışan modern bir masaüstü şifre yönetim uygulamasıdır.

Bulut sunucularına bağımlı kalmadan, hassas hesap bilgilerinizi kendi cihazınızda donanıma özel şifreleme algoritmalarıyla güvenle saklamanızı sağlar.

---

### 🌟 Öne Çıkan Özellikler

* 🛡️ **HWID Tabanlı Cihaz Bağlama:** Şifrelenmiş veri ve yedek dosyaları (`.json`), oluşturulduğu cihazın donanım kimliği (HWID) ile kilitlenir. Dışa aktarılan yedekler başka bir cihazda kesinlikle açılamaz.
* 🔒 **Tamamen Offline & Güvenli:** Hiçbir veri sunucuya aktarılmaz. Şifreleriniz ve güvenlik yanıtlarınız Fernet / AES-256 ve PBKDF2HMAC algoritmaları ile şifrelenir.
* 📋 **Akıllı Şifre Yöneticisi:** 
  * Türkçe karakter desteğine tam uyumlu alfabetik ve tarihsel sıralama (A-Z, Z-A, En Yeni, En Eski).
  * Tek tıkla kullanıcı adı ve şifre kopyalama (Clipboard).
  * Her şifre kaydına ait detaylı **İşlem Geçmişi (History Log)** takibi.
  * Esnek kayıt oluşturma (zorunlu alan kısıtlaması yok).
* 💾 **Güvenli Yedekleme & Geri Yükleme:** Masaüstüne donanım kilitli şifreli JSON yedeği alma ve tek tıkla geri yükleme.
* 🎨 **Gelişmiş Arayüz & Özelleştirme:** 
  * Açık, Koyu ve Sistem Varsayılanı tema seçenekleri.
  * Tam profesyonel çoklu dil desteği (Türkçe, İngilizce, Rusça) ve otomatik sistem dili algılama.
  * Pencere boyutu ve ekran konumu hatırlama hafızası.
  * Başlangıçta çalıştırma ve Sistem Tepsisine (System Tray) küçültme desteği.

---

### 🛠️ Teknolojiler

- **Dil:** Python 3.13+
- **GUI Framework:** CustomTkinter
- **Güvenlik & Şifreleme:** Cryptography (Fernet / PBKDF2), Hashlib
- **Sistem Entegrasyonu:** Pystray (System Tray), PyInstaller, Resource Hacker

---

> **Powered by Nova X Software**  
> *Geliştirici:* M. Miraç Özdemir (`@ozdmmrrc`)  
> *İletişim:* softwarenovax@gmail.com