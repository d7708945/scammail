import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import threading
import time

# Укажите адрес вашего сервера Amvera или локального запуска
API_BASE = "https://scam-scamhost.amvera.io//api"

class ScamMessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ScamMessenger")
        self.token = None
        self.phone = None
        self.running = True

        # --- UI ---
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Номер телефона:").grid(row=0, column=0, sticky="w")
        self.phone_entry = tk.Entry(frame, width=25)
        self.phone_entry.grid(row=0, column=1, sticky="we")
        tk.Button(frame, text="Регистрация", command=self.register).grid(row=0, column=2)

        tk.Label(frame, text="Код из SMS:").grid(row=1, column=0, sticky="w")
        self.code_entry = tk.Entry(frame, width=10)
        self.code_entry.grid(row=1, column=1, sticky="w")
        tk.Button(frame, text="Подтвердить", command=self.verify).grid(row=1, column=2)

        self.chat = scrolledtext.ScrolledText(frame, height=15, state="disabled")
        self.chat.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=8)

        self.msg_entry = tk.Entry(frame, width=50)
        self.msg_entry.grid(row=3, column=0, columnspan=2, sticky="we")
        tk.Button(frame, text="Отправить", command=self.send).grid(row=3, column=2)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        # Фоновая загрузка сообщений
        threading.Thread(target=self.poll_messages, daemon=True).start()

    # --- API методы ---
    def register(self):
        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showerror("Ошибка", "Введите номер телефона")
            return
        try:
            r = requests.post(f"{API_BASE}/register", json={"phone": phone}, timeout=5)
            data = r.json()
            if r.ok:
                self.phone = phone
                # Автовставка кода 1111
                self.code_entry.delete(0, tk.END)
                self.code_entry.insert(0, data.get("code", "1111"))
                messagebox.showinfo("OK", "Код отправлен (авто 1111)")
            else:
                messagebox.showerror("Ошибка", data.get("error", "fail"))
        except Exception as e:
            messagebox.showerror("Ошибка сети", str(e))

    def verify(self):
        code = self.code_entry.get().strip()
        if not self.phone:
            messagebox.showerror("Ошибка", "Сначала зарегистрируйтесь")
            return
        try:
            r = requests.post(f"{API_BASE}/verify", json={"phone": self.phone, "code": code}, timeout=5)
            data = r.json()
            if r.ok:
                self.token = data["token"]
                messagebox.showinfo("OK", "Подтверждено")
            else:
                messagebox.showerror("Ошибка", data.get("error", "fail"))
        except Exception as e:
            messagebox.showerror("Ошибка сети", str(e))

    def poll_messages(self):
        while self.running:
            try:
                r = requests.get(f"{API_BASE}/messages", timeout=5)
                data = r.json()
                msgs = data.get("messages", [])
                self.chat.configure(state="normal")
                self.chat.delete("1.0", tk.END)
                for m in msgs:
                    line = f"[{m['ts']}] {m['user_id'][:6]}: {m['text']}\n"
                    self.chat.insert(tk.END, line)
                self.chat.configure(state="disabled")
            except Exception:
                pass
            time.sleep(2)

    def send(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        if not self.token:
            messagebox.showerror("Ошибка", "Нужно подтвердить номер")
            return
        try:
            r = requests.post(f"{API_BASE}/messages", json={"token": self.token, "text": text}, timeout=5)
            if r.ok:
                self.msg_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Ошибка", r.json().get("error", "fail"))
        except Exception as e:
            messagebox.showerror("Ошибка сети", str(e))

    def close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScamMessengerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
