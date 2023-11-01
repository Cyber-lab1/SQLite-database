import sqlite3
import pyotp
import getpass
import qrcode
import base64
import io
from colorama import init, Fore, Style
import emoji


init(autoreset=True)

conn = sqlite3.connect('SQLite.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    totp_secret TEXT
                )''')

def hash_password(password):
    return base64.b64encode(password.encode()).decode()

def validate_password(username, password):
    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    stored_password_hash = cursor.fetchone()
    if stored_password_hash and hash_password(password) == stored_password_hash[0]:
        return True
    return False

def setup_2fa(username):
    top_secret = pyotp.random_base32()
    cursor.execute("UPDATE users SET top_secret = ? WHERE username = ?", (top_secret, username))
    conn.commit()
    print(Fore.GREEN + "✅2FA has been set up for your account.")
    print(Fore.GREEN + "Please use the following QR code to set up your 2FA app:")
    totp = pyotp.TOTP(top_secret)
    uri = totp.provisioning_uri(username, issuer_name="YourApp")
    img = qrcode.make(uri)
    img.save("qrcode.png")
    img.show()


def validate_2fa(username, input_2fa_code):
    cursor.execute("SELECT top_secret FROM users WHERE username=?", (username,))
    stored_secret = cursor.fetchone()
    if stored_secret:
        totp = pyotp.TOTP(stored_secret[0])
        return totp.verify(input_2fa_code)
    return False

def register_user(username, password):
    pass_hash = hash_password(password)
    cursor.execute("INSERT INTO users (username, pass_hash) VALUES (?, ?)", (username, pass_hash))
    conn.commit()
    print(Fore.GREEN + " ✅ ✅ User registered succssfully.")

def login(username):
    password = getpass.getpass("Enter your password: ")
    if validate_password(username, password):
        if not cursor.execute("SELECT totp_secret FROM users WHERE username=?", (username,)).fetchone():
            print(Fore.RED + "❌ 2FA is not set up for your account. Please set it up first.")
        else:
            input_2fa_code = input("Enter your 2FA code: ")
            if validate_2fa(username, input_2fa_code):
                print(Fore.GREEN + "✅Login successful.")
            else:
                print(Fore.RED + " ❌  Invalid 2FA code.")
    else:
        print(Fore.RED + " ❌  Invalid password.")


while True:
    print(Fore.CYAN + """
      ____        _    _  _____ _      _____ _     
     / ___| _ __ (_)  / \|_   _| |    |_   _| |    
    | |  _ | '_ \| | / _ \ | | | |      | | | |    
    | |_| || | | | / ___ \| | | |___   | | | |___ 
     \____| |_| |_/_/   \_\_| |_____|  |_| |_____|
        """)

    print(Fore.MAGENTA + "Choose an option:")
    print(Fore.MAGENTA + "1. Register")
    print(Fore.MAGENTA + "2. Login")
    print(Fore.MAGENTA + "3. Set up 2FA")
    print(Fore.MAGENTA + "4. Exit")

    choice = input(Fore.MAGENTA + "Enter your choice: ")

    if choice == "1":
        username = input("Enter a username: ")
        password = getpass.getpass("Enter a password: ")
        register_user(username, password)
    elif choice == "2":
        username = input("Enter your username: ")
        login(username)
    elif choice == "3":
        username = input("Enter your username: ")
        setup_2fa(username)
    elif choice == "4":
        break

conn.close()