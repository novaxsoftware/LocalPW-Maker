#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LocalPW Maker - Secure Local Password Manager (v5)
===================================================
Single-file desktop application.

New in v5:
  - Sorting (AZ/ZA/Newest/Oldest) with Turkish collation
  - Optional fields — at least Platform OR Username
  - Bold/larger typography
  - History button (G / H / И) with modal
  - Debounced search + lightweight list refresh
"""

import sys

# --- DPI awareness (must be before any GUI import) ---
if sys.platform.startswith("win"):
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    except Exception:
        pass

import os
import re
import json
import base64
import secrets
import locale
import subprocess
import threading
import time
import webbrowser
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog

try:
    import customtkinter as ctk
except ImportError:
    print("Kurulum gerekli: pip install customtkinter cryptography pystray Pillow")
    sys.exit(1)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

try:
    from PIL import Image, ImageDraw, ImageTk
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False
    Image = ImageDraw = ImageTk = None
    pystray = None


# ============================================================
#  SABİTLER
# ============================================================
APP_NAME = "LocalPW Maker"
APP_DIR = os.path.join(os.path.expanduser("~"), ".localpw_maker")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
VAULT_PATH = os.path.join(APP_DIR, "vault.enc")

NOVA_URL = "https://www.itemsatis.com/p/mich"
INSTA_URL = "https://www.instagram.com/ozdmmrrc/"
EMAIL = "softwarenovax@gmail.com"

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 680
DEFAULT_SORT = "az"
COLUMN_WEIGHTS = [3, 4, 4, 5, 0]

# ---- Tipografi (kalın ve okunaklı) ----
FONT_BASE = 13
FONT_SMALL = 12
FONT_BOLD = 14
FONT_SECTION = 17
FONT_HEADER = 19
FONT_TITLE = 22
FONT_TAB = 14
FONT_ICON = 15


# ============================================================
#  ÇEVİRİLER
# ============================================================
TRANSLATIONS = {
    "tr": {
        "app_title": "LocalPW Maker",
        "splash_subtitle": "Güvenli Yerel Şifre Yöneticisi",
        "setup_title": "İlk Kurulum",
        "setup_subtitle": "Güvenli kasanızı oluşturun",
        "login_title": "Giriş",
        "login_subtitle": "Master şifrenizle giriş yapın",
        "reset_title": "Şifre Sıfırlama",
        "reset_subtitle": "Güvenlik sorusu ile şifrenizi sıfırlayın",
        "master_password": "Master Şifre",
        "password": "Şifre",
        "password_confirm": "Şifre (Tekrar)",
        "security_question": "Güvenlik Sorusu",
        "security_answer": "Güvenlik Cevabı",
        "new_master_password": "Yeni Master Şifre",
        "confirm_new_master_password": "Yeni Master Şifre (Tekrar)",
        "create": "Oluştur",
        "login": "Giriş Yap",
        "forgot_password": "Şifremi Unuttum",
        "reset": "Sıfırla",
        "cancel": "İptal",
        "close": "Kapat",
        "error": "Hata",
        "passwords_do_not_match": "Şifreler eşleşmiyor!",
        "all_fields_required": "Lütfen tüm alanları doldurun.",
        "at_least_one_required": "En az bir alan doldurulmalıdır (Platform veya Kullanıcı Adı).",
        "wrong_password": "Hatalı şifre!",
        "wrong_answer": "Hatalı güvenlik cevabı!",
        "reset_success": "Şifreniz başarıyla sıfırlandı.",
        "too_short": "Şifre en az 4 karakter olmalıdır.",
        "tab_passwords": "Şifre Yöneticisi",
        "tab_backup": "Yedek İşlemleri",
        "tab_settings": "Ayarlar",
        "tab_faq": "SSS",
        "faq_title": "Sıkça Sorulan Sorular",
        "search_placeholder": "Ara...",
        "sort_by": "Sıralama",
        "sort_az": "Alfabetik (A-Z)",
        "sort_za": "Alfabetik (Z-A)",
        "sort_newest": "En Yeni",
        "sort_oldest": "En Eski",
        "add_new": "Yeni Ekle",
        "platform": "Platform",
        "username": "Kullanıcı Adı",
        "notes": "Notlar",
        "actions": "İşlemler",
        "save": "Kaydet",
        "delete": "Sil",
        "edit": "Düzenle",
        "history_btn": "G",
        "history_title": "İşlem Geçmişi",
        "history_created": "Şifre Oluşturuldu",
        "history_updated": "Şifre Güncellendi",
        "history_copied_username": "Kullanıcı Adı Kopyalandı",
        "history_copied_password": "Şifre Kopyalandı",
        "history_empty": "Bu kayıt için henüz geçmiş yok.",
        "no_records": "Henüz kayıt yok.",
        "new_record": "Yeni Şifre Kaydı",
        "edit_record": "Kaydı Düzenle",
        "delete_confirm_title": "Silme Onayı",
        "delete_confirm_msg": "Bu kaydı silmek istediğinize emin misiniz?",
        "backup_take": "Yedek Al",
        "backup_restore": "Yedek Geri Yükle",
        "backup_take_desc": "Tüm verileriniz şifrelenerek Masaüstüne kaydedilir.",
        "backup_restore_desc": "Daha önce aldığınız yedeği geri yükleyin.",
        "backup_saved": "Masaüstüne kaydedildi.",
        "backup_success": "Yedek başarıyla geri yüklendi.",
        "backup_wrong_device": "Bu yedek dosyası sadece oluşturulduğu cihazda açılabilir!",
        "backup_invalid": "Geçersiz yedek dosyası!",
        "backup_fail": "Yedek işlemi başarısız oldu.",
        "backup_select": "Yedek dosyası seç",
        "appearance": "Görünüm",
        "theme": "Tema",
        "light": "Açık",
        "dark": "Koyu",
        "system": "Sistem",
        "language": "Dil",
        "turkish": "Türkçe",
        "english": "İngilizce",
        "russian": "Rusça",
        "system_options": "Sistem Seçenekleri",
        "start_on_boot": "Başlangıçta Çalıştır",
        "minimize_to_tray": "Sistem Tepsisine Küçült",
        "about": "Hakkında",
        "powered_by": "powered by",
        "contact": "İletişim",
        "change_password": "Şifre Değiştir",
        "old_password": "Eski Şifre",
        "new_password": "Yeni Şifre",
        "confirm_new_password": "Yeni Şifre (Tekrar)",
        "change": "Değiştir",
        "password_changed": "Şifreniz başarıyla değiştirildi.",
        "copied": "Kopyalandı!",
        "tooltip_master": "En az 4 karakterli, unutmayacağınız bir şifre belirleyin.",
        "tooltip_security": "Şifrenizi unutursanız bu soruyla sıfırlayabilirsiniz.",
        "tooltip_search": "Kayıtlar arasında arama yapın.",
        "tooltip_sort": "Listeyi farklı ölçütlere göre sıralayın.",
        "tooltip_password": "Şifreyi göster/gizle yapabilirsiniz.",
        "tooltip_backup": "Yedek dosyası yalnızca bu cihazda açılır.",
        "tooltip_theme": "Uygulama temasını değiştirin.",
        "tooltip_language": "Arayüz dilini değiştirin.",
        "tooltip_startup": "Windows başlangıcında otomatik çalıştır.",
        "tooltip_tray": "Pencereyi kapatınca sistem tepsisine küçült.",
        "tooltip_change_password": "Eski şifrenizi doğrulayarak yeni bir şifre belirleyin.",
        "tooltip_copy": "Panoya kopyala",
        "tooltip_history": "İşlem geçmişini görüntüle",
        "tray_tooltip": "LocalPW Maker",
        "tray_show": "Göster",
        "tray_quit": "Çıkış",
        "security_questions": [
            "İlk evcil hayvanınızın adı nedir?",
            "Annenizin kızlık soyadı nedir?",
            "İlk okulunuzun adı nedir?",
            "En sevdiğiniz şehir neresi?",
            "Çocukluğunuzdaki en iyi arkadaşınızın adı?",
        ],
        "faq_items": [
            ("Bilgilerim nasıl saklanıyor?",
             "Program cihazınızın donanımlarına özel bir HWİD oluşturur. HWİD ise şifreli şekilde cihazın hafızasında saklanır."),
            ("Yedek dosyasını başka cihazda açabilir miyim?",
             "Hayır, açamazsınız. Güvenlik amaçlı bilgiler sadece oluşturulan cihazda tekrar yüklenebilir."),
            ("Bilgilerim başka bir sistem veya sunucuda saklanıyor mu?",
             "Hayır, program tamamen local olarak çalışır. Hiçbir veri dışa aktarılmaz."),
            ("Yedekleme işlemi nasıl gerçekleşir?",
             "Kaydettiğiniz şifreler ve cihaz HWİD'i ile şifrelenerek bir json dosyası haline getirilir ve masaüstüne kaydedilir."),
        ],
    },
    "en": {
        "app_title": "LocalPW Maker",
        "splash_subtitle": "Secure Local Password Manager",
        "setup_title": "First Setup",
        "setup_subtitle": "Create your secure vault",
        "login_title": "Login",
        "login_subtitle": "Log in with your master password",
        "reset_title": "Password Reset",
        "reset_subtitle": "Reset your password with the security question",
        "master_password": "Master Password",
        "password": "Password",
        "password_confirm": "Password (Repeat)",
        "security_question": "Security Question",
        "security_answer": "Security Answer",
        "new_master_password": "New Master Password",
        "confirm_new_master_password": "New Master Password (Repeat)",
        "create": "Create",
        "login": "Log In",
        "forgot_password": "Forgot Password",
        "reset": "Reset",
        "cancel": "Cancel",
        "close": "Close",
        "error": "Error",
        "passwords_do_not_match": "Passwords do not match!",
        "all_fields_required": "Please fill all fields.",
        "at_least_one_required": "At least one field must be filled (Platform or Username).",
        "wrong_password": "Wrong password!",
        "wrong_answer": "Wrong security answer!",
        "reset_success": "Your password was reset successfully.",
        "too_short": "Password must be at least 4 characters.",
        "tab_passwords": "Password Manager",
        "tab_backup": "Backup",
        "tab_settings": "Settings",
        "tab_faq": "FAQ",
        "faq_title": "Frequently Asked Questions",
        "search_placeholder": "Search...",
        "sort_by": "Sort",
        "sort_az": "Alphabetical (A-Z)",
        "sort_za": "Alphabetical (Z-A)",
        "sort_newest": "Newest First",
        "sort_oldest": "Oldest First",
        "add_new": "Add New",
        "platform": "Platform",
        "username": "Username",
        "notes": "Notes",
        "actions": "Actions",
        "save": "Save",
        "delete": "Delete",
        "edit": "Edit",
        "history_btn": "H",
        "history_title": "History",
        "history_created": "Password Created",
        "history_updated": "Password Updated",
        "history_copied_username": "Username Copied",
        "history_copied_password": "Password Copied",
        "history_empty": "No history for this record yet.",
        "no_records": "No records yet.",
        "new_record": "New Password Record",
        "edit_record": "Edit Record",
        "delete_confirm_title": "Confirm Delete",
        "delete_confirm_msg": "Are you sure you want to delete this record?",
        "backup_take": "Create Backup",
        "backup_restore": "Restore Backup",
        "backup_take_desc": "All your data is encrypted and saved to Desktop.",
        "backup_restore_desc": "Restore a previously created backup.",
        "backup_saved": "Saved to Desktop.",
        "backup_success": "Backup restored successfully.",
        "backup_wrong_device": "This backup can only be opened on the device it was created!",
        "backup_invalid": "Invalid backup file!",
        "backup_fail": "Backup operation failed.",
        "backup_select": "Select backup file",
        "appearance": "Appearance",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "system": "System",
        "language": "Language",
        "turkish": "Turkish",
        "english": "English",
        "russian": "Russian",
        "system_options": "System Options",
        "start_on_boot": "Run at Startup",
        "minimize_to_tray": "Minimize to Tray",
        "about": "About",
        "powered_by": "powered by",
        "contact": "Contact",
        "change_password": "Change Password",
        "old_password": "Old Password",
        "new_password": "New Password",
        "confirm_new_password": "New Password (Repeat)",
        "change": "Change",
        "password_changed": "Password changed successfully.",
        "copied": "Copied!",
        "tooltip_master": "Choose a password of at least 4 characters you won't forget.",
        "tooltip_security": "You can reset your password with this question if you forget it.",
        "tooltip_search": "Search among records.",
        "tooltip_sort": "Sort the list by different criteria.",
        "tooltip_password": "Show/hide the password.",
        "tooltip_backup": "Backup file can only be opened on this device.",
        "tooltip_theme": "Change the application theme.",
        "tooltip_language": "Change the interface language.",
        "tooltip_startup": "Run automatically on Windows startup.",
        "tooltip_tray": "Minimize to system tray when window is closed.",
        "tooltip_change_password": "Verify your old password and set a new one.",
        "tooltip_copy": "Copy to clipboard",
        "tooltip_history": "View history",
        "tray_tooltip": "LocalPW Maker",
        "tray_show": "Show",
        "tray_quit": "Quit",
        "security_questions": [
            "What was your first pet's name?",
            "What is your mother's maiden name?",
            "What was the name of your first school?",
            "What is your favorite city?",
            "What was your best childhood friend's name?",
        ],
        "faq_items": [
            ("How is my information stored?",
             "The program generates a HWID unique to your device's hardware. The HWID is stored encrypted on the device's memory."),
            ("Can I open the backup file on another device?",
             "No, you cannot. For security reasons, data can only be restored on the device where it was created."),
            ("Is my information stored on another system or server?",
             "No, the program runs entirely locally. No data is exported."),
            ("How does the backup process work?",
             "Your saved passwords are encrypted with the device HWID and turned into a json file saved to the desktop."),
        ],
    },
    "ru": {
        "app_title": "LocalPW Maker",
        "splash_subtitle": "Безопасный локальный менеджер паролей",
        "setup_title": "Первая настройка",
        "setup_subtitle": "Создайте безопасное хранилище",
        "login_title": "Вход",
        "login_subtitle": "Войдите с помощью мастер-пароля",
        "reset_title": "Сброс пароля",
        "reset_subtitle": "Сбросьте пароль с помощью контрольного вопроса",
        "master_password": "Мастер-пароль",
        "password": "Пароль",
        "password_confirm": "Пароль (повтор)",
        "security_question": "Контрольный вопрос",
        "security_answer": "Контрольный ответ",
        "new_master_password": "Новый мастер-пароль",
        "confirm_new_master_password": "Новый мастер-пароль (повтор)",
        "create": "Создать",
        "login": "Войти",
        "forgot_password": "Забыли пароль?",
        "reset": "Сбросить",
        "cancel": "Отмена",
        "close": "Закрыть",
        "error": "Ошибка",
        "passwords_do_not_match": "Пароли не совпадают!",
        "all_fields_required": "Пожалуйста, заполните все поля.",
        "at_least_one_required": "Заполните хотя бы одно поле (Платформа или Имя пользователя).",
        "wrong_password": "Неверный пароль!",
        "wrong_answer": "Неверный контрольный ответ!",
        "reset_success": "Пароль успешно сброшен.",
        "too_short": "Пароль должен содержать не менее 4 символов.",
        "tab_passwords": "Менеджер паролей",
        "tab_backup": "Резервные копии",
        "tab_settings": "Настройки",
        "tab_faq": "ЧЗВ",
        "faq_title": "Часто задаваемые вопросы",
        "search_placeholder": "Поиск...",
        "sort_by": "Сортировка",
        "sort_az": "По алфавиту (А-Я)",
        "sort_za": "По алфавиту (Я-А)",
        "sort_newest": "Сначала новые",
        "sort_oldest": "Сначала старые",
        "add_new": "Добавить",
        "platform": "Платформа",
        "username": "Имя пользователя",
        "notes": "Заметки",
        "actions": "Действия",
        "save": "Сохранить",
        "delete": "Удалить",
        "edit": "Изменить",
        "history_btn": "И",
        "history_title": "История",
        "history_created": "Пароль создан",
        "history_updated": "Пароль обновлён",
        "history_copied_username": "Имя пользователя скопировано",
        "history_copied_password": "Пароль скопирован",
        "history_empty": "Записей истории пока нет.",
        "no_records": "Записей пока нет.",
        "new_record": "Новая запись пароля",
        "edit_record": "Изменить запись",
        "delete_confirm_title": "Подтверждение удаления",
        "delete_confirm_msg": "Вы уверены, что хотите удалить эту запись?",
        "backup_take": "Создать резервную копию",
        "backup_restore": "Восстановить резервную копию",
        "backup_take_desc": "Все данные шифруются и сохраняются на Рабочий стол.",
        "backup_restore_desc": "Восстановите ранее созданную резервную копию.",
        "backup_saved": "Сохранено на Рабочий стол.",
        "backup_success": "Резервная копия успешно восстановлена.",
        "backup_wrong_device": "Эту резервную копию можно открыть только на устройстве, где она была создана!",
        "backup_invalid": "Неверный файл резервной копии!",
        "backup_fail": "Не удалось выполнить операцию резервного копирования.",
        "backup_select": "Выберите файл резервной копии",
        "appearance": "Внешний вид",
        "theme": "Тема",
        "light": "Светлая",
        "dark": "Тёмная",
        "system": "Системная",
        "language": "Язык",
        "turkish": "Турецкий",
        "english": "Английский",
        "russian": "Русский",
        "system_options": "Системные параметры",
        "start_on_boot": "Запускать при старте",
        "minimize_to_tray": "Свернуть в трей",
        "about": "О программе",
        "powered_by": "powered by",
        "contact": "Контакты",
        "change_password": "Изменить пароль",
        "old_password": "Старый пароль",
        "new_password": "Новый пароль",
        "confirm_new_password": "Новый пароль (повтор)",
        "change": "Изменить",
        "password_changed": "Пароль успешно изменён.",
        "copied": "Скопировано!",
        "tooltip_master": "Выберите пароль не менее 4 символов, который вы не забудете.",
        "tooltip_security": "Вы сможете сбросить пароль с помощью этого вопроса.",
        "tooltip_search": "Поиск среди записей.",
        "tooltip_sort": "Сортировать список по разным критериям.",
        "tooltip_password": "Показать/скрыть пароль.",
        "tooltip_backup": "Резервная копия открывается только на этом устройстве.",
        "tooltip_theme": "Изменить тему приложения.",
        "tooltip_language": "Изменить язык интерфейса.",
        "tooltip_startup": "Автоматический запуск при старте Windows.",
        "tooltip_tray": "Сворачивать в трей при закрытии окна.",
        "tooltip_change_password": "Подтвердите старый пароль и задайте новый.",
        "tooltip_copy": "Копировать в буфер обмена",
        "tooltip_history": "Показать историю",
        "tray_tooltip": "LocalPW Maker",
        "tray_show": "Показать",
        "tray_quit": "Выход",
        "security_questions": [
            "Как звали вашего первого питомца?",
            "Девичья фамилия вашей матери?",
            "Название вашей первой школы?",
            "Ваш любимый город?",
            "Имя лучшего друга детства?",
        ],
        "faq_items": [
            ("Как хранится моя информация?",
             "Программа создаёт HWID, уникальный для аппаратного обеспечения вашего устройства. HWID хранится в зашифрованном виде в памяти устройства."),
            ("Могу ли я открыть резервную копию на другом устройстве?",
             "Нет, не можете. В целях безопасности данные можно восстановить только на том устройстве, где они были созданы."),
            ("Хранится ли моя информация в другой системе или на сервере?",
             "Нет, программа работает полностью локально. Никакие данные не передаются наружу."),
            ("Как происходит процесс резервного копирования?",
             "Ваши сохранённые пароли шифруются с помощью HWID устройства и преобразуются в json-файл, сохраняемый на рабочий стол."),
        ],
    },
}


# ============================================================
#  SIRALAMA (Türkçe / çoklu dil uyumlu)
# ============================================================
_TRANSLIT_MAP = {
    'ç': 'c', 'Ç': 'c',
    'ğ': 'g', 'Ğ': 'g',
    'ı': 'i', 'İ': 'i',
    'ö': 'o', 'Ö': 'o',
    'ş': 's', 'Ş': 's',
    'ü': 'u', 'Ü': 'u',
    'â': 'a', 'Â': 'a',
    'î': 'i', 'Î': 'i',
    'û': 'u', 'Û': 'u',
}


def collation_key(text) -> str:
    """Locale bağımsız, Türkçe karakter uyumlu sıralama anahtarı."""
    if not text:
        return ""
    s = str(text)
    for src, dst in _TRANSLIT_MAP.items():
        s = s.replace(src, dst)
    return s.lower()


# ============================================================
#  YARDIMCI FONKSİYONLAR
# ============================================================
def ensure_dirs():
    os.makedirs(APP_DIR, exist_ok=True)


def b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode()


def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode())


def pbkdf2(password: bytes, salt: bytes, iterations: int = 200_000, length: int = 32) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=length, salt=salt, iterations=iterations)
    return kdf.derive(password)


def format_ts(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str or "-"


_HWID_CACHE = None


def get_hwid() -> str:
    global _HWID_CACHE
    if _HWID_CACHE:
        return _HWID_CACHE
    try:
        if sys.platform.startswith("win"):
            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                stderr=subprocess.DEVNULL, creationflags=0x08000000,
            ).decode(errors="ignore")
            lines = [l.strip() for l in out.splitlines() if l.strip() and "UUID" not in l.upper()]
            if lines:
                _HWID_CACHE = lines[0]
                return _HWID_CACHE
        elif sys.platform == "darwin":
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
            ).decode(errors="ignore")
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    _HWID_CACHE = line.split("=")[-1].strip().strip('"')
                    return _HWID_CACHE
        else:
            with open("/etc/machine-id") as f:
                _HWID_CACHE = f.read().strip()
                return _HWID_CACHE
    except Exception:
        pass
    import uuid as _uuid
    _HWID_CACHE = f"{_uuid.getnode():012x}"
    return _HWID_CACHE


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_config(cfg: dict):
    ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def detect_system_language() -> str:
    candidates = []
    try:
        loc = locale.getlocale()
        if loc and loc[0]:
            candidates.append(loc[0])
    except Exception:
        pass
    try:
        loc = locale.getdefaultlocale()
        if loc and loc[0]:
            candidates.append(loc[0])
    except Exception:
        pass
    try:
        lang_env = os.environ.get("LANG") or os.environ.get("LC_ALL") or os.environ.get("LANGUAGE")
        if lang_env:
            candidates.append(lang_env)
    except Exception:
        pass
    if sys.platform.startswith("win"):
        try:
            import ctypes
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            lang_code = {0x041F: "tr", 0x0409: "en", 0x0419: "ru"}.get(lang_id)
            if lang_code:
                return lang_code
        except Exception:
            pass
    for c in candidates:
        if not c:
            continue
        c_low = str(c).lower()
        if c_low.startswith("tr"):
            return "tr"
        if c_low.startswith("ru"):
            return "ru"
        if c_low.startswith("en"):
            return "en"
    return "en"


def center_window(window, width, height):
    """Pencereyi ekranın TAM ortasına yerleştirir."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.update_idletasks()


def make_app_icon(size: int = 64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 64.0
    d.rounded_rectangle([12 * s, 28 * s, 52 * s, 58 * s], radius=int(6 * s), fill="#3b82f6")
    d.arc([20 * s, 12 * s, 44 * s, 36 * s], start=180, end=360, fill="#3b82f6", width=int(6 * s))
    d.ellipse([28 * s, 38 * s, 36 * s, 46 * s], fill="#ffffff")
    d.rectangle([30 * s, 44 * s, 34 * s, 52 * s], fill="#ffffff")
    return img


# ============================================================
#  TOOLTIP & INFO IKON & TOAST
# ============================================================
class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _colors(self):
        mode = ctk.get_appearance_mode()
        return ("#f0f0f0", "#000000") if mode == "Dark" else ("#1f2937", "#ffffff")

    def _show(self, _=None):
        if self.tip:
            return
        bg, fg = self._colors()
        x = self.widget.winfo_pointerx() + 15
        y = self.widget.winfo_pointery() + 15
        try:
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_attributes("-topmost", True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(
                self.tip, text=self.text, bg=bg, fg=fg,
                padx=10, pady=6, font=("Segoe UI", 10, "bold"),
                justify="left", wraplength=280,
            ).pack()
        except Exception:
            self.tip = None

    def _hide(self, _=None):
        if self.tip:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None


def info_icon(parent, text: str):
    lbl = ctk.CTkLabel(
        parent, text="ⓘ", font=ctk.CTkFont(size=FONT_ICON, weight="bold"),
        text_color=("#3b82f6", "#60a5fa"), cursor="hand2",
    )
    Tooltip(lbl, text)
    return lbl


def show_toast(widget, msg: str, duration: int = 1200):
    try:
        toast = tk.Toplevel(widget)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        tk.Label(
            toast, text=msg, bg="#10b981", fg="white",
            padx=18, pady=8, font=("Segoe UI", 11, "bold"),
        ).pack()
        x = widget.winfo_pointerx() + 10
        y = widget.winfo_pointery() - 40
        toast.geometry(f"+{x}+{y}")

        def _dismiss():
            try:
                toast.destroy()
            except Exception:
                pass

        widget.after(duration, _dismiss)
    except Exception:
        pass


# ============================================================
#  SPLASH
# ============================================================
class SplashScreen:
    def __init__(self, root, app, on_done):
        self.root = root
        self.app = app
        self.on_done = on_done
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)

        w, h = 460, 340
        self.w, self.h = w, h
        self.bg = "#0b1220"
        self.accent = "#3b82f6"
        self.win.configure(bg=self.bg)

        self.canvas = tk.Canvas(self.win, width=w, height=h, bg=self.bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        center_window(self.win, w, h)

        self.angle = 0
        self.running = True
        self._draw_static()
        self._animate()

        try:
            self.win.attributes("-topmost", True)
            self.win.after(100, lambda: self.win.attributes("-topmost", False))
        except Exception:
            pass
        self.win.after(2600, self._finish)

    def _draw_static(self):
        c = self.canvas
        cx, cy = self.w // 2, 130
        c.create_oval(cx - 90, cy - 90, cx + 90, cy + 90, outline="#1e293b", width=1)
        c.create_rectangle(cx - 38, cy - 10, cx + 38, cy + 52, fill=self.accent, outline="")
        c.create_arc(cx - 26, cy - 50, cx + 26, cy + 6, start=0, extent=180,
                     style="arc", width=10, outline=self.accent)
        c.create_oval(cx - 7, cy + 10, cx + 7, cy + 24, fill=self.bg, outline="")
        c.create_rectangle(cx - 3, cy + 20, cx + 3, cy + 36, fill=self.bg, outline="")
        c.create_text(cx, 235, text="LocalPW Maker", fill="#ffffff",
                      font=("Segoe UI", 24, "bold"))
        subtitle = self.app.T("splash_subtitle") if self.app else "Secure Local Password Manager"
        c.create_text(cx, 268, text=subtitle, fill="#94a3b8", font=("Segoe UI", 11))

    def _animate(self):
        if not self.running:
            return
        c = self.canvas
        c.delete("spinner")
        cx, cy = self.w // 2, 305
        c.create_arc(cx - 16, cy - 16, cx + 16, cy + 16, start=self.angle, extent=90,
                     style="arc", width=4, outline=self.accent, tags="spinner")
        self.angle = (self.angle + 15) % 360
        self.win.after(40, self._animate)

    def _finish(self):
        self.running = False
        try:
            self.win.destroy()
        except Exception:
            pass
        self.on_done()


# ============================================================
#  TAB BAR
# ============================================================
class TabBar(ctk.CTkFrame):
    def __init__(self, master, tabs, on_change):
        super().__init__(master, fg_color="transparent")
        self.tabs = tabs
        self.on_change = on_change
        self.buttons = {}
        self.current = None
        for key, _label_fn in tabs:
            btn = ctk.CTkButton(
                self, text="", width=150, height=40, corner_radius=8,
                fg_color="transparent", border_width=1,
                border_color=("#d1d5db", "#374151"),
                text_color=("#1f2937", "#e5e7eb"),
                hover_color=("#e5e7eb", "#1f2937"),
                font=ctk.CTkFont(size=FONT_TAB, weight="bold"),
                command=lambda k=key: self.select(k),
            )
            btn.pack(side="left", padx=(0, 8))
            self.buttons[key] = btn
        self.refresh_texts()
        if tabs:
            self.select(tabs[0][0])

    def refresh_texts(self):
        for key, label_fn in self.tabs:
            try:
                self.buttons[key].configure(text=label_fn())
            except Exception:
                pass

    def select(self, key):
        self.current = key
        for k, b in self.buttons.items():
            try:
                if k == key:
                    b.configure(fg_color=("#3b82f6", "#2563eb"),
                                text_color="#ffffff",
                                border_color=("#3b82f6", "#2563eb"))
                else:
                    b.configure(fg_color="transparent",
                                text_color=("#1f2937", "#e5e7eb"),
                                border_color=("#d1d5db", "#374151"))
            except Exception:
                pass
        self.on_change(key)


# ============================================================
#  ŞİFRE YÖNETİCİSİ SAYFASI
# ============================================================
class PasswordPage:
    def __init__(self, master, app):
        self.app = app
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self.hidden_state = {}
        self.search_var = None
        self.sort_combo = None
        self._search_after_id = None
        self._build_ui_structure()
        self.refresh()

    # ---- Sabit İskelet (dil değişince yenilenir) ----
    def _build_ui_structure(self):
        # Top bar
        top = ctk.CTkFrame(self.frame, fg_color="transparent")
        top.pack(fill="x", padx=5, pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)

        search = ctk.CTkEntry(
            top, placeholder_text=self.app.T("search_placeholder"),
            textvariable=self.search_var, height=40,
            font=ctk.CTkFont(size=FONT_BASE),
        )
        search.pack(side="left", fill="x", expand=True)
        info_icon(top, self.app.T("tooltip_search")).pack(side="left", padx=(6, 10))

        # Sort label + dropdown
        sort_lbl = ctk.CTkLabel(
            top, text=self.app.T("sort_by") + ":",
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
        )
        sort_lbl.pack(side="left", padx=(0, 4))
        info_icon(top, self.app.T("tooltip_sort")).pack(side="left", padx=(0, 6))

        sort_options_display = [
            self.app.T("sort_az"),
            self.app.T("sort_za"),
            self.app.T("sort_newest"),
            self.app.T("sort_oldest"),
        ]
        mode_to_display = {"az": 0, "za": 1, "newest": 2, "oldest": 3}
        current_sort = (self.app.config or {}).get("sort_by", DEFAULT_SORT)
        if current_sort not in mode_to_display:
            current_sort = DEFAULT_SORT

        self.sort_combo = ctk.CTkComboBox(
            top, values=sort_options_display, width=185, height=40,
            font=ctk.CTkFont(size=FONT_BASE),
            command=self._on_sort_changed,
        )
        self.sort_combo.set(sort_options_display[mode_to_display[current_sort]])
        self.sort_combo.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top, text="+  " + self.app.T("add_new"), height=40, width=140,
            fg_color=("#3b82f6", "#2563eb"), hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=self.add_record,
        ).pack(side="left")

        # Header row
        header = ctk.CTkFrame(self.frame, fg_color=("#f3f4f6", "#111827"), corner_radius=6)
        header.pack(fill="x", padx=(2, 18), pady=(0, 4))
        for i, w in enumerate(COLUMN_WEIGHTS):
            header.grid_columnconfigure(i, weight=w)
        cols = [("platform", 14, "w"), ("username", 8, "w"),
                ("password", 8, "w"), ("notes", 8, "w"), ("actions", 10, "e")]
        for i, (key, pad, sticky) in enumerate(cols):
            ctk.CTkLabel(
                header, text=self.app.T(key),
                font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
                text_color=("#374151", "#d1d5db"),
            ).grid(row=0, column=i, sticky=sticky, padx=pad, pady=10)

        # Scroll
        self.scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

    # ---- Dil güncellemesi ----
    def update_language(self):
        old_search = self.search_var.get() if self.search_var else ""
        for w in self.frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self._build_ui_structure()
        if old_search:
            self.search_var.set(old_search)  # triggers trace → refresh
        else:
            self.refresh()

    # ---- Arama debounce ----
    def _on_search_changed(self, *_):
        if self._search_after_id:
            try:
                self.frame.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.frame.after(180, self.refresh)

    # ---- Sıralama ----
    def _on_sort_changed(self, value):
        try:
            display_to_mode = {
                self.app.T("sort_az"): "az",
                self.app.T("sort_za"): "za",
                self.app.T("sort_newest"): "newest",
                self.app.T("sort_oldest"): "oldest",
            }
            mode = display_to_mode.get(value, DEFAULT_SORT)
            if self.app.config is None:
                self.app.config = {}
            self.app.config["sort_by"] = mode
            save_config(self.app.config)
        except Exception:
            pass
        self.refresh()

    def _apply_sort(self, items):
        mode = (self.app.config or {}).get("sort_by", DEFAULT_SORT)
        try:
            if mode == "az":
                return sorted(items, key=lambda it: collation_key(it.get("platform", "")))
            if mode == "za":
                return sorted(items, key=lambda it: collation_key(it.get("platform", "")), reverse=True)
            if mode == "newest":
                return sorted(items, key=lambda it: it.get("created_at", ""), reverse=True)
            if mode == "oldest":
                return sorted(items, key=lambda it: it.get("created_at", ""))
        except Exception:
            pass
        return items

    # ---- Hafif refresh (yalnızca scroll içeriği) ----
    def refresh(self):
        for w in self.scroll.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        q = (self.search_var.get() if self.search_var else "").strip().lower()
        items = list(self.app.data)
        if q:
            items = [
                it for it in items
                if q in it.get("platform", "").lower()
                or q in it.get("username", "").lower()
            ]
        items = self._apply_sort(items)

        if not items:
            ctk.CTkLabel(
                self.scroll, text=self.app.T("no_records"),
                text_color=("#6b7280", "#9ca3af"),
                font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            ).pack(pady=60)
            return
        for item in items:
            self._render_row(item)

    # ---- Kopyala + geçmiş kaydı ----
    def _copy(self, text: str, item=None, field=None):
        try:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(text)
            self.app.root.update_idletasks()
            show_toast(self.app.root, self.app.T("copied"))

            if item is not None and field is not None:
                now_iso = datetime.utcnow().isoformat()
                item.setdefault("history", []).append({
                    "timestamp": now_iso,
                    "action": f"copied_{field}",
                })
                self.app.save_vault()
        except Exception:
            pass

    # ---- Satır render ----
    def _render_row(self, item):
        row = ctk.CTkFrame(self.scroll, corner_radius=10,
                           fg_color=("#ffffff", "#1f2937"),
                           border_width=1,
                           border_color=("#e5e7eb", "#374151"))
        row.pack(fill="x", pady=4, padx=2)
        for i, w in enumerate(COLUMN_WEIGHTS):
            row.grid_columnconfigure(i, weight=w)

        # Platform
        platform_txt = item.get("platform", "") or "-"
        ctk.CTkLabel(
            row, text=platform_txt,
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=12)

        # Username + copy
        uname = item.get("username", "")
        user_cell = ctk.CTkFrame(row, fg_color="transparent")
        user_cell.grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(
            user_cell, text=uname or "-",
            font=ctk.CTkFont(size=FONT_BASE),
            text_color=("#374151", "#d1d5db"),
        ).pack(side="left")
        if uname:
            btn = ctk.CTkButton(
                user_cell, text="📋", width=28, height=24,
                fg_color="transparent",
                hover_color=("#e5e7eb", "#374151"),
                text_color=("#374151", "#d1d5db"),
                font=ctk.CTkFont(size=FONT_SMALL),
                command=lambda t=uname, it=item: self._copy(t, it, "username"),
            )
            btn.pack(side="left", padx=(4, 0))
            Tooltip(btn, self.app.T("tooltip_copy"))

        # Password + eye + copy
        pwd = item.get("password", "")
        pw_cell = ctk.CTkFrame(row, fg_color="transparent")
        pw_cell.grid(row=0, column=2, sticky="w", padx=8)
        item_id = item.get("id", "")
        visible = not self.hidden_state.get(item_id, True)
        pw_label = ctk.CTkLabel(
            pw_cell, text=(pwd if visible else "•" * 8) if pwd else "-",
            font=ctk.CTkFont(size=FONT_BASE, family="Consolas"),
        )
        pw_label.pack(side="left")

        if pwd:
            def toggle(i=item_id, lbl=pw_label, it=item):
                self.hidden_state[i] = not self.hidden_state.get(i, True)
                lbl.configure(text=it.get("password", "") if not self.hidden_state[i] else "•" * 8)

            ctk.CTkButton(
                pw_cell, text="👁", width=28, height=24,
                fg_color="transparent",
                hover_color=("#e5e7eb", "#374151"),
                text_color=("#374151", "#d1d5db"),
                font=ctk.CTkFont(size=FONT_SMALL),
                command=toggle,
            ).pack(side="left", padx=(4, 0))

            btn = ctk.CTkButton(
                pw_cell, text="📋", width=28, height=24,
                fg_color="transparent",
                hover_color=("#e5e7eb", "#374151"),
                text_color=("#374151", "#d1d5db"),
                font=ctk.CTkFont(size=FONT_SMALL),
                command=lambda t=pwd, it=item: self._copy(t, it, "password"),
            )
            btn.pack(side="left", padx=(4, 0))
            Tooltip(btn, self.app.T("tooltip_copy"))

        # Notes
        ctk.CTkLabel(
            row, text=item.get("notes", "") or "-",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=("#6b7280", "#9ca3af"),
            anchor="w", justify="left",
        ).grid(row=0, column=3, sticky="we", padx=8)

        # Actions: Edit / Delete / History
        act = ctk.CTkFrame(row, fg_color="transparent")
        act.grid(row=0, column=4, sticky="e", padx=10)

        ctk.CTkButton(
            act, text=self.app.T("edit"), width=68, height=30,
            fg_color=("#f3f4f6", "#374151"),
            hover_color=("#e5e7eb", "#4b5563"),
            text_color=("#1f2937", "#e5e7eb"),
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            command=lambda it=item: self.edit_record(it),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            act, text=self.app.T("delete"), width=68, height=30,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b"),
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            command=lambda it=item: self.delete_record(it),
        ).pack(side="left", padx=3)

        hist_btn = ctk.CTkButton(
            act, text=self.app.T("history_btn"), width=38, height=30,
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            command=lambda it=item: self._show_history_dialog(it),
        )
        hist_btn.pack(side="left", padx=3)
        Tooltip(hist_btn, self.app.T("tooltip_history"))

    # ---- CRUD ----
    def add_record(self):
        self._edit_dialog(None)

    def edit_record(self, item):
        self._edit_dialog(item)

    def delete_record(self, item):
        if messagebox.askyesno(
            self.app.T("delete_confirm_title"),
            self.app.T("delete_confirm_msg"),
            parent=self.app.root,
        ):
            self.app.data = [i for i in self.app.data if i.get("id") != item.get("id")]
            self.app.save_vault()
            self.refresh()

    def _edit_dialog(self, item):
        dlg = ctk.CTkToplevel(self.app.root)
        dlg.title(self.app.T("edit_record") if item else self.app.T("new_record"))
        dlg.resizable(False, False)
        dlg.transient(self.app.root)
        center_window(dlg, 480, 600)
        dlg.grab_set()

        pad = 22

        ctk.CTkLabel(dlg, text=self.app.T("platform"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w", padx=pad, pady=(18, 4))
        platform_e = ctk.CTkEntry(dlg, height=38, font=ctk.CTkFont(size=FONT_BASE))
        platform_e.pack(fill="x", padx=pad)
        if item:
            platform_e.insert(0, item.get("platform", ""))

        ctk.CTkLabel(dlg, text=self.app.T("username"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w", padx=pad, pady=(10, 4))
        username_e = ctk.CTkEntry(dlg, height=38, font=ctk.CTkFont(size=FONT_BASE))
        username_e.pack(fill="x", padx=pad)
        if item:
            username_e.insert(0, item.get("username", ""))

        ctk.CTkLabel(dlg, text=self.app.T("password"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w", padx=pad, pady=(10, 4))
        pw_row = ctk.CTkFrame(dlg, fg_color="transparent")
        pw_row.pack(fill="x", padx=pad)
        password_e = ctk.CTkEntry(pw_row, show="*", height=38, font=ctk.CTkFont(size=FONT_BASE))
        password_e.pack(side="left", fill="x", expand=True)
        if item:
            password_e.insert(0, item.get("password", ""))

        def toggle_pw():
            password_e.configure(show="" if password_e.cget("show") else "*")

        ctk.CTkButton(
            pw_row, text="👁", width=42, height=38,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            text_color=("#1f2937", "#e5e7eb"),
            font=ctk.CTkFont(size=FONT_SMALL),
            command=toggle_pw,
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(dlg, text=self.app.T("notes"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w", padx=pad, pady=(10, 4))
        notes_e = ctk.CTkTextbox(dlg, height=100, font=ctk.CTkFont(size=FONT_BASE))
        notes_e.pack(fill="x", padx=pad)
        if item:
            notes_e.insert("1.0", item.get("notes", ""))

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=pad, pady=20)

        def do_save():
            p = platform_e.get().strip()
            u = username_e.get().strip()
            pw = password_e.get()
            n = notes_e.get("1.0", "end").strip()

            # En az bir alan dolu olmalı (Platform veya Kullanıcı Adı)
            if not p and not u:
                messagebox.showerror(self.app.T("error"),
                                     self.app.T("at_least_one_required"), parent=dlg)
                return

            now_iso = datetime.utcnow().isoformat()

            if item:
                item["platform"] = p
                item["username"] = u
                item["password"] = pw
                item["notes"] = n
                item["updated_at"] = now_iso
                item.setdefault("history", []).append({
                    "timestamp": now_iso,
                    "action": "updated",
                })
            else:
                self.app.data.append({
                    "id": secrets.token_hex(8),
                    "platform": p,
                    "username": u,
                    "password": pw,
                    "notes": n,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "history": [{"timestamp": now_iso, "action": "created"}],
                })
            self.app.save_vault()
            # ★ Performans: sadece liste yenilenir, ana UI yeniden kurulmaz
            self.refresh()
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text=self.app.T("cancel"), width=110, height=38,
            fg_color="transparent", border_width=1,
            text_color=("#1f2937", "#e5e7eb"),
            hover_color=("#f3f4f6", "#374151"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=dlg.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row, text=self.app.T("save"), width=110, height=38,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=do_save,
        ).pack(side="right")

    # ---- Geçmiş modalı ----
    def _show_history_dialog(self, item):
        dlg = ctk.CTkToplevel(self.app.root)
        dlg.title(self.app.T("history_title"))
        dlg.resizable(False, False)
        dlg.transient(self.app.root)
        center_window(dlg, 540, 560)
        dlg.grab_set()

        platform = item.get("platform", "") or "-"
        header = ctk.CTkFrame(dlg, fg_color=("#8b5cf6", "#7c3aed"), height=70, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="🕘  " + self.app.T("history_title") + " — " + platform,
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
            text_color="#ffffff",
        ).pack(side="left", padx=22, pady=18)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        history = list(item.get("history", []))
        try:
            history = sorted(history, key=lambda h: h.get("timestamp", ""))
        except Exception:
            pass

        action_map = {
            "created": "history_created",
            "updated": "history_updated",
            "copied_username": "history_copied_username",
            "copied_password": "history_copied_password",
        }
        icon_map = {
            "created": "🆕",
            "updated": "✏️",
            "copied_username": "📋",
            "copied_password": "🔑",
        }

        if not history:
            ctk.CTkLabel(
                scroll, text=self.app.T("history_empty"),
                font=ctk.CTkFont(size=FONT_BASE),
                text_color=("#6b7280", "#9ca3af"),
            ).pack(pady=50)
        else:
            for h in history:
                ts = format_ts(h.get("timestamp", ""))
                action = h.get("action", "")
                action_text = self.app.T(action_map.get(action, "history_updated"))
                icon = icon_map.get(action, "•")

                row = ctk.CTkFrame(scroll, corner_radius=8,
                                   fg_color=("#ffffff", "#1f2937"),
                                   border_width=1,
                                   border_color=("#e5e7eb", "#374151"))
                row.pack(fill="x", pady=4, padx=2)

                ctk.CTkLabel(
                    row, text=icon, font=ctk.CTkFont(size=FONT_ICON),
                    width=32,
                ).pack(side="left", padx=(12, 4), pady=10)

                ctk.CTkLabel(
                    row, text=ts,
                    font=ctk.CTkFont(size=FONT_SMALL),
                    text_color=("#6b7280", "#9ca3af"),
                    width=150, anchor="w",
                ).pack(side="left", padx=(0, 8), pady=10)

                ctk.CTkLabel(
                    row, text=action_text,
                    font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
                    anchor="w",
                ).pack(side="left", fill="x", expand=True, pady=10)

        ctk.CTkButton(
            dlg, text=self.app.T("close"), height=38, width=120,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=dlg.destroy,
        ).pack(pady=(0, 16))


# ============================================================
#  YEDEK SAYFASI
# ============================================================
class BackupPage:
    def __init__(self, master, app):
        self.app = app
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self._build_ui_structure()

    def _build_ui_structure(self):
        for w in self.frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        card1 = ctk.CTkFrame(self.frame, corner_radius=12,
                             fg_color=("#ffffff", "#1f2937"),
                             border_width=1,
                             border_color=("#e5e7eb", "#374151"))
        card1.pack(fill="x", pady=(0, 15))

        title_row = ctk.CTkFrame(card1, fg_color="transparent")
        title_row.pack(fill="x", padx=22, pady=(20, 4))
        ctk.CTkLabel(
            title_row, text="📦  " + self.app.T("backup_take"),
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
        ).pack(side="left")
        info_icon(title_row, self.app.T("tooltip_backup")).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            card1, text=self.app.T("backup_take_desc"),
            text_color=("#6b7280", "#9ca3af"),
            font=ctk.CTkFont(size=FONT_BASE),
        ).pack(anchor="w", padx=22)
        ctk.CTkButton(
            card1, text=self.app.T("backup_take"),
            height=42, width=220,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=self.do_backup,
        ).pack(anchor="w", padx=22, pady=20)

        card2 = ctk.CTkFrame(self.frame, corner_radius=12,
                             fg_color=("#ffffff", "#1f2937"),
                             border_width=1,
                             border_color=("#e5e7eb", "#374151"))
        card2.pack(fill="x")

        title_row2 = ctk.CTkFrame(card2, fg_color="transparent")
        title_row2.pack(fill="x", padx=22, pady=(20, 4))
        ctk.CTkLabel(
            title_row2, text="♻️  " + self.app.T("backup_restore"),
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            card2, text=self.app.T("backup_restore_desc"),
            text_color=("#6b7280", "#9ca3af"),
            font=ctk.CTkFont(size=FONT_BASE),
        ).pack(anchor="w", padx=22)
        ctk.CTkButton(
            card2, text=self.app.T("backup_restore"),
            height=42, width=220,
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=self.do_restore,
        ).pack(anchor="w", padx=22, pady=20)

    def update_language(self):
        self._build_ui_structure()

    def _desktop_path(self):
        d = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(d):
            d = os.path.expanduser("~")
        return d

    def do_backup(self):
        try:
            hwid = get_hwid()
            salt = secrets.token_bytes(16)
            key = pbkdf2(hwid.encode(), salt)
            fernet = Fernet(base64.urlsafe_b64encode(key))
            payload = json.dumps({"data": self.app.data}, ensure_ascii=False).encode()
            token = fernet.encrypt(payload)
            import hashlib
            backup = {
                "app": "LocalPW Maker",
                "version": 1,
                "salt": b64e(salt),
                "hwid_hash": hashlib.sha256(hwid.encode()).hexdigest()[:16],
                "payload": token.decode(),
            }
            fname = f"LocalPW_backup_{int(time.time())}.json"
            path = os.path.join(self._desktop_path(), fname)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(backup, f, indent=2, ensure_ascii=False)
            messagebox.showinfo(
                self.app.T("backup_take"),
                f"{self.app.T('backup_saved')}\n\n{path}",
                parent=self.app.root,
            )
        except Exception as e:
            messagebox.showerror(
                self.app.T("error"),
                f"{self.app.T('backup_fail')}\n{e}",
                parent=self.app.root,
            )

    def do_restore(self):
        path = filedialog.askopenfilename(
            title=self.app.T("backup_select"),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            parent=self.app.root,
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                backup = json.load(f)
            salt = b64d(backup["salt"])
            payload = backup["payload"]
            hwid = get_hwid()
            key = pbkdf2(hwid.encode(), salt)
            fernet = Fernet(base64.urlsafe_b64encode(key))
            try:
                plaintext = fernet.decrypt(payload.encode())
            except InvalidToken:
                messagebox.showerror(
                    self.app.T("error"),
                    self.app.T("backup_wrong_device"),
                    parent=self.app.root,
                )
                return
            data = json.loads(plaintext.decode())
            self.app.data = data.get("data", [])
            self.app._migrate_records()
            self.app.save_vault()
            self.app.pages["passwords"].refresh()
            messagebox.showinfo(
                self.app.T("backup_restore"),
                self.app.T("backup_success"),
                parent=self.app.root,
            )
        except (KeyError, json.JSONDecodeError, ValueError):
            messagebox.showerror(
                self.app.T("error"),
                self.app.T("backup_invalid"),
                parent=self.app.root,
            )
        except Exception as e:
            messagebox.showerror(
                self.app.T("error"),
                f"{self.app.T('backup_fail')}\n{e}",
                parent=self.app.root,
            )


# ============================================================
#  SSS SAYFASI
# ============================================================
class FAQPage:
    def __init__(self, master, app):
        self.app = app
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self._expanded = {}
        self._build_ui_structure()

    def _build_ui_structure(self):
        for w in self.frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        ctk.CTkLabel(
            self.frame, text="❓  " + self.app.T("faq_title"),
            font=ctk.CTkFont(size=FONT_SECTION, weight="bold"),
        ).pack(anchor="w", pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        items = self.app.T("faq_items")
        if not isinstance(items, list):
            items = []

        for idx, item in enumerate(items):
            try:
                q, a = item[0], item[1]
            except (IndexError, TypeError):
                continue
            self._build_card(scroll, idx, q, a)

    def _build_card(self, parent, idx, question, answer):
        card = ctk.CTkFrame(parent, corner_radius=12,
                            fg_color=("#ffffff", "#1f2937"),
                            border_width=1,
                            border_color=("#e5e7eb", "#374151"))
        card.pack(fill="x", pady=6, padx=2)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            header, text=str(idx + 1),
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            text_color=("#3b82f6", "#60a5fa"),
            width=28, height=28,
            fg_color=("#eff6ff", "#1e3a8a"),
            corner_radius=14,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header, text=question,
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            anchor="w", justify="left",
        ).pack(side="left", fill="x", expand=True)

        answer_frame = ctk.CTkFrame(card, fg_color="transparent")
        ctk.CTkLabel(
            answer_frame, text=answer,
            font=ctk.CTkFont(size=FONT_BASE),
            text_color=("#374151", "#d1d5db"),
            anchor="w", justify="left",
            wraplength=820,
        ).pack(fill="x", padx=(50, 20), pady=(0, 16))

        is_open = self._expanded.get(idx, False)
        toggle_btn = ctk.CTkButton(
            header, text="▲" if is_open else "▼",
            width=36, height=30,
            fg_color="transparent",
            hover_color=("#e5e7eb", "#374151"),
            text_color=("#6b7280", "#9ca3af"),
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
        )
        toggle_btn.pack(side="right")

        if is_open:
            answer_frame.pack(fill="x")

        def toggle(i=idx, af=answer_frame, btn=toggle_btn):
            if af.winfo_ismapped():
                af.pack_forget()
                btn.configure(text="▼")
                self._expanded[i] = False
            else:
                af.pack(fill="x")
                btn.configure(text="▲")
                self._expanded[i] = True

        toggle_btn.configure(command=toggle)

    def update_language(self):
        self._build_ui_structure()


# ============================================================
#  AYARLAR SAYFASI
# ============================================================
class SettingsPage:
    def __init__(self, master, app):
        self.app = app
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self.theme_keys = ["light", "dark", "system"]
        self.lang_keys = ["tr", "en", "ru"]
        self._build_ui_structure()

    def update_language(self):
        self._build_ui_structure()

    def _build_ui_structure(self):
        for w in self.frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        app = self.app

        # GÖRÜNÜM
        card = ctk.CTkFrame(scroll, corner_radius=12,
                            fg_color=("#ffffff", "#1f2937"),
                            border_width=1,
                            border_color=("#e5e7eb", "#374151"))
        card.pack(fill="x", pady=(0, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(hdr, text="🎨  " + app.T("appearance"),
                     font=ctk.CTkFont(size=FONT_SECTION, weight="bold")).pack(side="left")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(6, 10))
        ctk.CTkLabel(row, text=app.T("theme"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).pack(side="left")
        info_icon(row, app.T("tooltip_theme")).pack(side="left", padx=(6, 20))

        theme_values = [app.T(k) for k in self.theme_keys]
        seg_theme = ctk.CTkSegmentedButton(
            row, values=theme_values, height=34, width=300,
            font=ctk.CTkFont(size=FONT_BASE),
        )
        seg_theme.pack(side="right")
        try:
            idx = self.theme_keys.index(app.theme)
        except ValueError:
            idx = 2
        seg_theme.set(theme_values[idx])
        seg_theme.configure(command=self._on_theme_changed)

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=22, pady=(0, 18))
        ctk.CTkLabel(row2, text=app.T("language"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).pack(side="left")
        info_icon(row2, app.T("tooltip_language")).pack(side="left", padx=(6, 20))

        lang_values = [
            app.T({"tr": "turkish", "en": "english", "ru": "russian"}[k])
            for k in self.lang_keys
        ]
        seg_lang = ctk.CTkSegmentedButton(
            row2, values=lang_values, height=34, width=300,
            font=ctk.CTkFont(size=FONT_BASE),
        )
        seg_lang.pack(side="right")
        try:
            idx = self.lang_keys.index(app.lang)
        except ValueError:
            idx = 1
        seg_lang.set(lang_values[idx])
        seg_lang.configure(command=self._on_language_changed)

        # SİSTEM
        card2 = ctk.CTkFrame(scroll, corner_radius=12,
                             fg_color=("#ffffff", "#1f2937"),
                             border_width=1,
                             border_color=("#e5e7eb", "#374151"))
        card2.pack(fill="x", pady=(0, 15))
        hdr2 = ctk.CTkFrame(card2, fg_color="transparent")
        hdr2.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(hdr2, text="⚙️  " + app.T("system_options"),
                     font=ctk.CTkFont(size=FONT_SECTION, weight="bold")).pack(side="left")

        if sys.platform.startswith("win"):
            r3 = ctk.CTkFrame(card2, fg_color="transparent")
            r3.pack(fill="x", padx=22, pady=8)
            ctk.CTkLabel(r3, text=app.T("start_on_boot"),
                         font=ctk.CTkFont(size=FONT_BASE, weight="bold")).pack(side="left")
            info_icon(r3, app.T("tooltip_startup")).pack(side="left", padx=(6, 20))
            sw_start = ctk.CTkSwitch(r3, text="",
                                     command=lambda: app.toggle_startup(sw_start.get()))
            sw_start.pack(side="right")
            if app.config and app.config.get("start_on_boot", False):
                sw_start.select()

        r4 = ctk.CTkFrame(card2, fg_color="transparent")
        r4.pack(fill="x", padx=22, pady=(8, 18))
        ctk.CTkLabel(r4, text=app.T("minimize_to_tray"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).pack(side="left")
        info_icon(r4, app.T("tooltip_tray")).pack(side="left", padx=(6, 20))
        sw_tray = ctk.CTkSwitch(r4, text="",
                                command=lambda: app.toggle_tray(sw_tray.get()))
        sw_tray.pack(side="right")
        if app.config and app.config.get("minimize_to_tray", True):
            sw_tray.select()
        if not HAS_TRAY:
            sw_tray.configure(state="disabled")

        # ŞİFRE DEĞİŞTİR
        card3 = ctk.CTkFrame(scroll, corner_radius=12,
                             fg_color=("#ffffff", "#1f2937"),
                             border_width=1,
                             border_color=("#e5e7eb", "#374151"))
        card3.pack(fill="x", pady=(0, 15))
        hdr3 = ctk.CTkFrame(card3, fg_color="transparent")
        hdr3.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(hdr3, text="🔑  " + app.T("change_password"),
                     font=ctk.CTkFont(size=FONT_SECTION, weight="bold")).pack(side="left")
        info_icon(hdr3, app.T("tooltip_change_password")).pack(side="left", padx=(8, 0))

        form = ctk.CTkFrame(card3, fg_color="transparent")
        form.pack(fill="x", padx=22, pady=(4, 18))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text=app.T("old_password"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=6)
        self.old_pw_e = ctk.CTkEntry(form, show="*", height=36, font=ctk.CTkFont(size=FONT_BASE))
        self.old_pw_e.grid(row=0, column=1, sticky="we", padx=(12, 0), pady=6)

        ctk.CTkLabel(form, text=app.T("new_password"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).grid(
            row=1, column=0, sticky="w", pady=6)
        self.new_pw_e = ctk.CTkEntry(form, show="*", height=36, font=ctk.CTkFont(size=FONT_BASE))
        self.new_pw_e.grid(row=1, column=1, sticky="we", padx=(12, 0), pady=6)

        ctk.CTkLabel(form, text=app.T("confirm_new_password"),
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold")).grid(
            row=2, column=0, sticky="w", pady=6)
        self.conf_pw_e = ctk.CTkEntry(form, show="*", height=36, font=ctk.CTkFont(size=FONT_BASE))
        self.conf_pw_e.grid(row=2, column=1, sticky="we", padx=(12, 0), pady=6)

        ctk.CTkButton(
            form, text=app.T("change"), height=40, width=180,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=self._change_password,
        ).grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))

        # MARKA
        brand = ctk.CTkFrame(scroll, fg_color="transparent")
        brand.pack(fill="x", pady=(20, 4))
        brand_inner = ctk.CTkFrame(brand, fg_color="transparent")
        brand_inner.pack()

        ctk.CTkLabel(
            brand_inner, text=app.T("powered_by") + " ",
            font=ctk.CTkFont(size=FONT_SMALL, slant="italic", weight="bold"),
            text_color=("#6b7280", "#9ca3af"),
        ).pack(side="left")

        nova = ctk.CTkLabel(
            brand_inner, text="Nova X Software",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold", slant="italic"),
            text_color=("#3b82f6", "#60a5fa"),
            cursor="hand2",
        )
        nova.pack(side="left")
        nova.bind("<Button-1>", lambda _e: webbrowser.open(NOVA_URL))
        nova.bind("<Enter>", lambda _e: nova.configure(text_color=("#1d4ed8", "#93c5fd")))
        nova.bind("<Leave>", lambda _e: nova.configure(text_color=("#3b82f6", "#60a5fa")))

        # İLETİŞİM
        contact = ctk.CTkFrame(scroll, fg_color="transparent")
        contact.pack(fill="x", pady=(0, 25))

        ig = ctk.CTkLabel(
            contact, text="📷  @ozdmmrrc",
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            text_color=("#3b82f6", "#60a5fa"),
            cursor="hand2",
        )
        ig.pack()
        ig.bind("<Button-1>", lambda _e: webbrowser.open(INSTA_URL))
        ig.bind("<Enter>", lambda _e: ig.configure(text_color=("#1d4ed8", "#93c5fd")))
        ig.bind("<Leave>", lambda _e: ig.configure(text_color=("#3b82f6", "#60a5fa")))

        ctk.CTkLabel(
            contact, text="✉  " + EMAIL,
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=("#6b7280", "#9ca3af"),
        ).pack(pady=(6, 0))

    # ---- Callbacks ----
    def _on_theme_changed(self, val):
        try:
            values = [self.app.T(k) for k in self.theme_keys]
            idx = values.index(val)
            self.app.set_theme(self.theme_keys[idx])
        except (ValueError, IndexError):
            pass

    def _on_language_changed(self, val):
        try:
            lang_names = {"tr": "turkish", "en": "english", "ru": "russian"}
            values = [self.app.T(lang_names[k]) for k in self.lang_keys]
            idx = values.index(val)
            new_lang = self.lang_keys[idx]
        except (ValueError, IndexError):
            return
        try:
            self.app.root.after(20, lambda: self.app.set_language(new_lang))
        except Exception:
            pass

    def _change_password(self):
        app = self.app
        old = self.old_pw_e.get()
        new = self.new_pw_e.get()
        conf = self.conf_pw_e.get()

        if not old or not new or not conf:
            messagebox.showerror(app.T("error"), app.T("all_fields_required"), parent=app.root)
            return
        if new != conf:
            messagebox.showerror(app.T("error"), app.T("passwords_do_not_match"), parent=app.root)
            return
        if len(new) < 4:
            messagebox.showerror(app.T("error"), app.T("too_short"), parent=app.root)
            return

        try:
            hwid = get_hwid()
            salt = b64d(app.config["master_salt"])
            stored = b64d(app.config["master_hash"])
            if not secrets.compare_digest(pbkdf2(old.encode(), salt), stored):
                messagebox.showerror(app.T("error"), app.T("wrong_password"), parent=app.root)
                return
        except Exception:
            messagebox.showerror(app.T("error"), app.T("backup_fail"), parent=app.root)
            return

        if not getattr(app, "fernet_key_bytes", None):
            messagebox.showerror(app.T("error"), app.T("backup_fail"), parent=app.root)
            return

        try:
            new_salt = secrets.token_bytes(16)
            new_kek = pbkdf2((new + "|" + hwid).encode(), new_salt)
            new_fk_master = Fernet(base64.urlsafe_b64encode(new_kek)).encrypt(app.fernet_key_bytes)

            app.config["master_salt"] = b64e(new_salt)
            app.config["master_hash"] = b64e(pbkdf2(new.encode(), new_salt))
            app.config["fernet_key_master"] = new_fk_master.decode()
            save_config(app.config)

            self.old_pw_e.delete(0, "end")
            self.new_pw_e.delete(0, "end")
            self.conf_pw_e.delete(0, "end")

            messagebox.showinfo(
                app.T("change_password"),
                app.T("password_changed"),
                parent=app.root,
            )
        except Exception as e:
            messagebox.showerror(app.T("error"), str(e), parent=app.root)


# ============================================================
#  ANA UYGULAMA
# ============================================================
class App:
    def __init__(self):
        ensure_dirs()
        self.root = ctk.CTk()
        self.root.withdraw()

        self.config = load_config()
        if self.config is None:
            self.lang = detect_system_language()
            self.theme = "system"
        else:
            self.lang = self.config.get("language") or "en"
            if self.lang not in TRANSLATIONS:
                self.lang = "en"
            self.theme = self.config.get("theme", "system")
            if self.theme not in ("light", "dark", "system"):
                self.theme = "system"

        ctk.set_appearance_mode(self.theme)

        self.fernet = None
        self.fernet_key_bytes = None
        self.data = []
        self.tray = None
        self.auth_win = None
        self.pages = {}
        self.tabbar = None
        self.splash = None
        self._icon_photo = None

        self.root.after(50, self._start)

    def T(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["tr"]).get(key, key)

    def _start(self):
        self.splash = SplashScreen(self.root, self, on_done=self._after_splash)

    def _after_splash(self):
        if self.config is None:
            self.show_setup()
        else:
            self.show_login()

    # -------- KURULUM --------
    def show_setup(self):
        w = ctk.CTkToplevel(self.root)
        self.auth_win = w
        w.title(self.T("setup_title"))
        w.resizable(False, False)
        w.protocol("WM_DELETE_WINDOW", self.quit_app)
        center_window(w, 480, 720)

        header = ctk.CTkFrame(w, fg_color=("#2563eb", "#1d4ed8"),
                              height=130, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🔒", font=ctk.CTkFont(size=42)).pack(pady=(18, 0))
        ctk.CTkLabel(header, text=self.T("setup_title"),
                     font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
                     text_color="#ffffff").pack()
        ctk.CTkLabel(header, text=self.T("setup_subtitle"),
                     font=ctk.CTkFont(size=FONT_SMALL),
                     text_color="#dbeafe").pack(pady=(0, 14))

        body = ctk.CTkFrame(w, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=20)

        r = ctk.CTkFrame(body, fg_color="transparent")
        r.pack(fill="x")
        ctk.CTkLabel(r, text=self.T("password"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(side="left")
        info_icon(r, self.T("tooltip_master")).pack(side="left", padx=(6, 0))
        mp_e = ctk.CTkEntry(body, show="*", placeholder_text="••••••••",
                            height=40, font=ctk.CTkFont(size=FONT_BASE))
        mp_e.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(body, text=self.T("password_confirm"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        cmp_e = ctk.CTkEntry(body, show="*", placeholder_text="••••••••",
                             height=40, font=ctk.CTkFont(size=FONT_BASE))
        cmp_e.pack(fill="x", pady=(4, 12))

        r2 = ctk.CTkFrame(body, fg_color="transparent")
        r2.pack(fill="x")
        ctk.CTkLabel(r2, text=self.T("security_question"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(side="left")
        info_icon(r2, self.T("tooltip_security")).pack(side="left", padx=(6, 0))
        q_defaults = self.T("security_questions")
        q_var = tk.StringVar(value=q_defaults[0])
        ctk.CTkComboBox(body, values=q_defaults, variable=q_var, height=40,
                        font=ctk.CTkFont(size=FONT_BASE)).pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(body, text=self.T("security_answer"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        sa_e = ctk.CTkEntry(body, height=40, font=ctk.CTkFont(size=FONT_BASE))
        sa_e.pack(fill="x", pady=(4, 22))

        def do_create():
            mp = mp_e.get()
            cmp_ = cmp_e.get()
            ans = sa_e.get().strip()
            q = q_var.get().strip()
            if not mp or not cmp_ or not ans or not q:
                messagebox.showerror(self.T("error"), self.T("all_fields_required"), parent=w)
                return
            if len(mp) < 4:
                messagebox.showerror(self.T("error"), self.T("too_short"), parent=w)
                return
            if mp != cmp_:
                messagebox.showerror(self.T("error"), self.T("passwords_do_not_match"), parent=w)
                return

            hwid = get_hwid()
            fernet_key = secrets.token_bytes(32)
            master_salt = secrets.token_bytes(16)
            answer_salt = secrets.token_bytes(16)

            master_hash = pbkdf2(mp.encode(), master_salt)
            answer_hash = pbkdf2(ans.lower().encode(), answer_salt)

            master_kek = pbkdf2((mp + "|" + hwid).encode(), master_salt)
            answer_kek = pbkdf2((ans.lower() + "|" + hwid).encode(), answer_salt)

            fk_master = Fernet(base64.urlsafe_b64encode(master_kek)).encrypt(fernet_key)
            fk_answer = Fernet(base64.urlsafe_b64encode(answer_kek)).encrypt(fernet_key)

            cfg = {
                "version": 1,
                "master_salt": b64e(master_salt),
                "master_hash": b64e(master_hash),
                "question": q,
                "answer_salt": b64e(answer_salt),
                "answer_hash": b64e(answer_hash),
                "fernet_key_master": fk_master.decode(),
                "fernet_key_answer": fk_answer.decode(),
                "language": self.lang,
                "theme": self.theme,
                "start_on_boot": False,
                "minimize_to_tray": True,
                "sort_by": DEFAULT_SORT,
            }
            self.config = cfg
            save_config(cfg)

            self.fernet_key_bytes = fernet_key
            self.fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
            self.data = []
            self.save_vault()

            w.destroy()
            self._on_auth_success()

        ctk.CTkButton(
            body, text=self.T("create"), height=46,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            command=do_create,
        ).pack(fill="x")

        w.after(120, lambda: (w.lift(), w.focus_force(), mp_e.focus_set()))

    # -------- GİRİŞ --------
    def show_login(self):
        w = ctk.CTkToplevel(self.root)
        self.auth_win = w
        w.title(self.T("login_title"))
        w.resizable(False, False)
        w.protocol("WM_DELETE_WINDOW", self.quit_app)
        center_window(w, 460, 500)

        header = ctk.CTkFrame(w, fg_color=("#2563eb", "#1d4ed8"),
                              height=140, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🔐", font=ctk.CTkFont(size=44)).pack(pady=(20, 0))
        ctk.CTkLabel(header, text=self.T("login_title"),
                     font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
                     text_color="#ffffff").pack()
        ctk.CTkLabel(header, text=self.T("login_subtitle"),
                     font=ctk.CTkFont(size=FONT_SMALL),
                     text_color="#dbeafe").pack(pady=(0, 14))

        body = ctk.CTkFrame(w, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(body, text=self.T("master_password"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        mp_e = ctk.CTkEntry(body, show="*", placeholder_text="••••••••",
                            height=42, font=ctk.CTkFont(size=FONT_BASE))
        mp_e.pack(fill="x", pady=(4, 18))

        def do_login():
            mp = mp_e.get()
            if not mp:
                return
            if self.verify_master(mp):
                w.destroy()
                self._on_auth_success()
            else:
                messagebox.showerror(self.T("error"), self.T("wrong_password"), parent=w)
                mp_e.delete(0, "end")

        ctk.CTkButton(
            body, text=self.T("login"), height=46,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            command=do_login,
        ).pack(fill="x")

        forgot = ctk.CTkLabel(
            body, text=self.T("forgot_password"),
            font=ctk.CTkFont(size=FONT_BASE, underline=True, weight="bold"),
            text_color=("#3b82f6", "#60a5fa"), cursor="hand2",
        )
        forgot.pack(pady=(18, 0))
        forgot.bind("<Button-1>", lambda _e: (w.destroy(), self.show_reset()))

        w.bind("<Return>", lambda _e: do_login())
        w.after(120, lambda: (w.lift(), w.focus_force(), mp_e.focus_set()))

    # -------- SIFIRLAMA --------
    def show_reset(self):
        w = ctk.CTkToplevel(self.root)
        self.auth_win = w
        w.title(self.T("reset_title"))
        w.resizable(False, False)
        w.protocol("WM_DELETE_WINDOW", self.quit_app)
        center_window(w, 460, 660)

        header = ctk.CTkFrame(w, fg_color=("#dc2626", "#991b1b"),
                              height=120, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🔑", font=ctk.CTkFont(size=40)).pack(pady=(18, 0))
        ctk.CTkLabel(header, text=self.T("reset_title"),
                     font=ctk.CTkFont(size=FONT_TITLE, weight="bold"),
                     text_color="#ffffff").pack()
        ctk.CTkLabel(header, text=self.T("reset_subtitle"),
                     font=ctk.CTkFont(size=FONT_SMALL),
                     text_color="#fecaca").pack(pady=(0, 14))

        body = ctk.CTkFrame(w, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=20)

        ctk.CTkLabel(body, text=self.T("security_question") + ":",
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(body, text=self.config.get("question", ""),
                     font=ctk.CTkFont(size=FONT_BASE),
                     text_color=("#374151", "#d1d5db"),
                     wraplength=380, justify="left").pack(anchor="w", pady=(2, 12))

        ctk.CTkLabel(body, text=self.T("security_answer"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        ans_e = ctk.CTkEntry(body, height=40, font=ctk.CTkFont(size=FONT_BASE))
        ans_e.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(body, text=self.T("new_master_password"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        new_e = ctk.CTkEntry(body, show="*", height=40, font=ctk.CTkFont(size=FONT_BASE))
        new_e.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(body, text=self.T("confirm_new_master_password"),
                     font=ctk.CTkFont(size=FONT_BOLD, weight="bold")).pack(anchor="w")
        confirm_e = ctk.CTkEntry(body, show="*", height=40, font=ctk.CTkFont(size=FONT_BASE))
        confirm_e.pack(fill="x", pady=(4, 22))

        def do_reset():
            ans = ans_e.get().strip().lower()
            new_mp = new_e.get()
            confirm = confirm_e.get()
            if not ans or not new_mp or not confirm:
                messagebox.showerror(self.T("error"), self.T("all_fields_required"), parent=w)
                return
            if new_mp != confirm:
                messagebox.showerror(self.T("error"), self.T("passwords_do_not_match"), parent=w)
                return
            if len(new_mp) < 4:
                messagebox.showerror(self.T("error"), self.T("too_short"), parent=w)
                return

            hwid = get_hwid()
            ans_salt = b64d(self.config["answer_salt"])
            stored = b64d(self.config["answer_hash"])
            if not secrets.compare_digest(pbkdf2(ans.encode(), ans_salt), stored):
                messagebox.showerror(self.T("error"), self.T("wrong_answer"), parent=w)
                return

            answer_kek = pbkdf2((ans + "|" + hwid).encode(), ans_salt)
            try:
                fk = Fernet(base64.urlsafe_b64encode(answer_kek)).decrypt(
                    self.config["fernet_key_answer"].encode()
                )
            except InvalidToken:
                messagebox.showerror(self.T("error"), self.T("backup_wrong_device"), parent=w)
                return

            master_salt = secrets.token_bytes(16)
            master_kek = pbkdf2((new_mp + "|" + hwid).encode(), master_salt)
            fk_master = Fernet(base64.urlsafe_b64encode(master_kek)).encrypt(fk)

            self.config["master_salt"] = b64e(master_salt)
            self.config["master_hash"] = b64e(pbkdf2(new_mp.encode(), master_salt))
            self.config["fernet_key_master"] = fk_master.decode()
            save_config(self.config)

            self.fernet_key_bytes = fk
            self.fernet = Fernet(base64.urlsafe_b64encode(fk))
            messagebox.showinfo(self.T("reset_title"), self.T("reset_success"), parent=w)
            w.destroy()
            self._on_auth_success()

        ctk.CTkButton(
            body, text=self.T("reset"), height=44,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b"),
            font=ctk.CTkFont(size=FONT_BOLD, weight="bold"),
            command=do_reset,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body, text=self.T("cancel"), height=38,
            fg_color="transparent", border_width=1,
            text_color=("#1f2937", "#e5e7eb"),
            hover_color=("#f3f4f6", "#374151"),
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=lambda: (w.destroy(), self.show_login()),
        ).pack(fill="x")

        w.after(120, lambda: (w.lift(), w.focus_force(), ans_e.focus_set()))

    def verify_master(self, mp: str) -> bool:
        try:
            hwid = get_hwid()
            salt = b64d(self.config["master_salt"])
            stored = b64d(self.config["master_hash"])
            computed = pbkdf2(mp.encode(), salt)
            if not secrets.compare_digest(computed, stored):
                return False
            kek = pbkdf2((mp + "|" + hwid).encode(), salt)
            fk = Fernet(base64.urlsafe_b64encode(kek)).decrypt(
                self.config["fernet_key_master"].encode()
            )
            self.fernet_key_bytes = fk
            self.fernet = Fernet(base64.urlsafe_b64encode(fk))
            return True
        except (InvalidToken, KeyError, ValueError):
            return False

    # -------- KASA --------
    def load_vault(self):
        if not os.path.exists(VAULT_PATH):
            self.data = []
            return
        try:
            with open(VAULT_PATH, "rb") as f:
                token = f.read().strip()
            if not token:
                self.data = []
                return
            plaintext = self.fernet.decrypt(token)
            self.data = json.loads(plaintext.decode())
        except Exception:
            self.data = []

    def save_vault(self):
        if self.fernet is None:
            return
        ensure_dirs()
        token = self.fernet.encrypt(json.dumps(self.data, ensure_ascii=False).encode())
        with open(VAULT_PATH, "wb") as f:
            f.write(token)

    def _migrate_records(self):
        """Eski kayıtlara created_at / updated_at / history ekle."""
        changed = False
        now_iso = datetime.utcnow().isoformat()
        for rec in self.data:
            if "created_at" not in rec:
                rec["created_at"] = now_iso
                changed = True
            if "updated_at" not in rec:
                rec["updated_at"] = rec["created_at"]
                changed = True
            if "history" not in rec:
                rec["history"] = [{"timestamp": rec["created_at"], "action": "created"}]
                changed = True
        if changed:
            self.save_vault()

    # -------- PENCERE GEOMETRİSİ --------
    def _apply_saved_geometry(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if self.config:
            geom = self.config.get("window_geometry")
            if geom:
                try:
                    m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geom)
                    if m:
                        w, h, x, y = map(int, m.groups())
                        w = max(900, min(w, sw))
                        h = max(600, min(h, sh))
                        x = max(-w + 100, min(x, sw - 100))
                        y = max(0, min(y, sh - 100))
                        self.root.geometry(f"{w}x{h}+{x}+{y}")
                        self.root.update_idletasks()
                        return
                except Exception:
                    pass

        x = (sw // 2) - (DEFAULT_WIDTH // 2)
        y = (sh // 2) - (DEFAULT_HEIGHT // 2)
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}+{x}+{y}")
        self.root.update_idletasks()

    def _save_geometry(self):
        try:
            if self.root.state() == "normal" and self.root.winfo_viewable():
                geom = (f"{self.root.winfo_width()}x{self.root.winfo_height()}"
                        f"+{self.root.winfo_x()}+{self.root.winfo_y()}")
                if self.config is None:
                    self.config = {}
                self.config["window_geometry"] = geom
                save_config(self.config)
        except Exception:
            pass

    # -------- KİMLİK DOĞRULAMA SONRASI --------
    def _on_auth_success(self):
        self.load_vault()
        self._migrate_records()
        self.root.title(APP_NAME)
        self.root.minsize(900, 600)
        try:
            img = make_app_icon(64)
            self._icon_photo = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, self._icon_photo)
        except Exception:
            pass
        self._build_main_content()
        self._build_tray()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._apply_saved_geometry()
        self.root.deiconify()
        self.root.update_idletasks()
        try:
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _build_main_content(self):
        header = ctk.CTkFrame(self.root, fg_color=("#f9fafb", "#111827"),
                              height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="🔒  " + APP_NAME,
            font=ctk.CTkFont(size=FONT_HEADER, weight="bold"),
        ).pack(side="left", padx=22)

        self.tabbar = TabBar(
            self.root,
            tabs=[
                ("passwords", lambda: "🔐  " + self.T("tab_passwords")),
                ("backup",    lambda: "📦  " + self.T("tab_backup")),
                ("settings",  lambda: "⚙️  " + self.T("tab_settings")),
                ("faq",       lambda: "❓  " + self.T("tab_faq")),
            ],
            on_change=self._on_tab_change,
        )
        self.tabbar.pack(fill="x", padx=22, pady=(14, 8))

        self.content = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        self.pages = {
            "passwords": PasswordPage(self.content, self),
            "backup":    BackupPage(self.content, self),
            "settings":  SettingsPage(self.content, self),
            "faq":       FAQPage(self.content, self),
        }
        for p in self.pages.values():
            p.frame.pack_forget()
        self.pages["passwords"].frame.pack(fill="both", expand=True)
        if self.tabbar.current:
            self.tabbar.select(self.tabbar.current)

    def _on_tab_change(self, key):
        for p in self.pages.values():
            try:
                p.frame.pack_forget()
            except Exception:
                pass
        if key in self.pages:
            try:
                self.pages[key].frame.pack(fill="both", expand=True)
            except Exception:
                pass

    def set_theme(self, theme):
        self.theme = theme
        if self.config is None:
            self.config = {}
        self.config["theme"] = theme
        save_config(self.config)
        try:
            ctk.set_appearance_mode(theme)
        except Exception:
            pass

    def set_language(self, lang):
        if lang not in TRANSLATIONS:
            lang = "en"
        self.lang = lang
        if self.config is None:
            self.config = {}
        self.config["language"] = lang
        save_config(self.config)
        self._update_language()

    def _update_language(self):
        try:
            if self.tabbar:
                self.tabbar.refresh_texts()
        except Exception:
            pass
        for key, page in list(self.pages.items()):
            try:
                if hasattr(page, "update_language"):
                    page.update_language()
            except Exception:
                pass
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
            self.tray = None
        self._build_tray()
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass

    def toggle_startup(self, enabled: bool):
        if not sys.platform.startswith("win"):
            return
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            if enabled:
                exe = sys.executable
                script = os.path.abspath(__file__)
                if exe.lower().endswith("python.exe"):
                    cmd = f'"{exe}" "{script}"'
                else:
                    cmd = f'"{exe}"'
                winreg.SetValueEx(key, "LocalPW Maker", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "LocalPW Maker")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            if self.config is None:
                self.config = {}
            self.config["start_on_boot"] = enabled
            save_config(self.config)
        except Exception as e:
            messagebox.showerror(self.T("error"), str(e), parent=self.root)

    def toggle_tray(self, enabled: bool):
        if self.config is None:
            self.config = {}
        self.config["minimize_to_tray"] = enabled
        save_config(self.config)

    def _build_tray(self):
        if not HAS_TRAY or not (self.config or {}).get("minimize_to_tray", True):
            self.tray = None
            return
        try:
            img = make_app_icon(64)
            menu = pystray.Menu(
                pystray.MenuItem(self.T("tray_show"), self._tray_show, default=True),
                pystray.MenuItem(self.T("tray_quit"), self._tray_quit),
            )
            self.tray = pystray.Icon("LocalPW", img, self.T("tray_tooltip"), menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            self.tray = None

    def _tray_show(self, _icon=None, _item=None):
        try:
            self.root.after(0, self._restore_from_tray)
        except Exception:
            pass

    def _tray_quit(self, _icon=None, _item=None):
        try:
            self.root.after(0, self.force_quit)
        except Exception:
            pass

    def _restore_from_tray(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def on_close(self):
        self._save_geometry()
        minimize = (self.config or {}).get("minimize_to_tray", True)
        if minimize and self.tray is not None:
            try:
                self.root.withdraw()
            except Exception:
                pass
        else:
            self.force_quit()

    def force_quit(self):
        self._save_geometry()
        try:
            if self.tray:
                self.tray.stop()
                self.tray = None
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def quit_app(self):
        self.force_quit()

    def run(self):
        self.root.mainloop()


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    App().run()