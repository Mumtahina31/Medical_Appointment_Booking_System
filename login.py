import tkinter as tk
from tkinter import messagebox
import sqlite3

# --- Database Setup ---
conn = sqlite3.connect("mydb.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,s
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'teacher'))
)
""")
conn.commit()

# --- Main Application ---
root = tk.Tk()
root.title("Login System")
root.geometry("400x300")

# --- GUI Components ---
def clear_entries():
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)

def register():
    username = username_entry.get()
    password = password_entry.get()
    role = role_var.get()

    if not username or not password or role not in ['Patient', 'Doctor']:
        messagebox.showerror("Error", "All fields are required.")
        return

    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
        messagebox.showinfo("Success", f"{role.capitalize()} registered successfully.")
        clear_entries()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")

def login():
    username = username_entry.get()
    password = password_entry.get()

    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()

    if result:
        role = result[0]
        messagebox.showinfo("Login Success", f"Welcome {role.capitalize()} {username}!")
        show_role_window(username, role)
    else:
        messagebox.showerror("Error", "Invalid username or password.")

def show_role_window(username, role):
    new_window = tk.Toplevel(root)
    new_window.title(f"{role.capitalize()} Dashboard")
    new_window.geometry("300x200")
    label = tk.Label(new_window, text=f"Welcome, {role.capitalize()} {username}!", font=("Arial", 14))
    label.pack(pady=40)

# --- Widgets Layout ---
tk.Label(root, text="Username:").pack(pady=(20, 5))
username_entry = tk.Entry(root, width=30)
username_entry.pack()

tk.Label(root, text="Password:").pack(pady=(10, 5))
password_entry = tk.Entry(root, show='*', width=30)
password_entry.pack()

tk.Label(root, text="Role:").pack(pady=(10, 5))
role_var = tk.StringVar(value="[patient]")
tk.Radiobutton(root, text="Patient", variable=role_var, value="Patient").pack()
tk.Radiobutton(root, text="Doctor", variable=role_var, value="Doctor").pack()

tk.Button(root, text="Register", command=register, bg="green", fg="white").pack(pady=(15, 5))
tk.Button(root, text="Login", command=login, bg="blue", fg="white").pack()

# --- Start GUI Loop ---
root.mainloop()
conn.close()
