import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import datetime
import re

# --- Configuración de la base de datos ---
conn = sqlite3.connect('finanzasapp.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    balance REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    transaction_type TEXT,
    amount REAL,
    date TEXT,
    status TEXT)''')
conn.commit()

# --- Funciones de validación ---
def validar_usuario(username):
    if not username.strip():
        return "El nombre de usuario no puede estar vacío."
    if username.strip() != username:
        return "El nombre de usuario no debe tener espacios al inicio o al final."
    if not username.isalpha():
        return "El nombre de usuario solo debe contener letras."
    return None

def validar_contraseña(password):
    if len(password) < 4:
        return "La contraseña debe tener al menos 4 caracteres."
    return None

def validar_saldo(saldo):
    if saldo < 0:
        return "El saldo inicial no puede ser negativo."
    return None

def user_exists(username):
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    return c.fetchone() is not None

# --- Funciones de base de datos ---
def register_user(username, password, initial_balance=1000):
    err = validar_usuario(username) or validar_contraseña(password) or validar_saldo(initial_balance)
    if err:
        st.error(err)
        return False

    if user_exists(username):
        st.error("El usuario ya existe.")
        return False

    c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
              (username, password, initial_balance))
    conn.commit()
    return True

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def create_transaction(user_id, transaction_type, amount):
    if amount <= 0:
        st.error("El monto debe ser mayor a cero.")
        return

    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        st.error("Usuario no encontrado.")
        return

    balance = result[0]

    if transaction_type == "Retiro" and amount > balance:
        st.error("Saldo insuficiente para realizar esta transacción.")
        return

    new_balance = balance - amount if transaction_type == "Retiro" else balance + amount
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    c.execute("INSERT INTO transactions (user_id, transaction_type, amount, date, status) VALUES (?, ?, ?, ?, ?)",
              (user_id, transaction_type, amount, date, "completada"))
    conn.commit()
    st.success(f"{transaction_type} de ${amount:.2f} realizada correctamente.")

def get_transactions(user_id):
    c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    return c.fetchall()

def get_user_balance(user_id):
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    return result[0] if result else 0

# --- Interfaz de usuario ---
st.title("FinanzasApp - Gestión Financiera")
menu = ["Inicio", "Registro", "Login", "Realizar Transacción", "Ver Transacciones", "Ver Balance"]
choice = st.sidebar.selectbox("Menú", menu)

if choice == "Registro":
    st.subheader("Registro de Usuario")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    initial_balance = st.number_input("Saldo inicial", min_value=0.0, value=1000.0)
    if st.button("Registrar"):
        if register_user(username, password, initial_balance):
            st.success("Usuario registrado correctamente.")

elif choice == "Login":
    st.subheader("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    if st.button("Ingresar"):
        if not username or not password:
            st.error("Por favor, complete ambos campos.")
        else:
            user = login_user(username, password)
            if user:
                st.session_state['user'] = user
                st.success(f"Bienvenido {user[1]}")
            else:
                st.error("Usuario o contraseña incorrectos.")

elif choice == "Realizar Transacción":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión primero.")
    else:
        st.subheader("Realizar Transacción")
        transaction_type = st.selectbox("Tipo de transacción", ["Ingreso", "Retiro"])
        amount = st.number_input("Monto", min_value=0.01)
        if st.button("Realizar"):
            create_transaction(st.session_state['user'][0], transaction_type, amount)

elif choice == "Ver Transacciones":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión primero.")
    else:
        st.subheader("Historial de Transacciones")
        transactions = get_transactions(st.session_state['user'][0])
        if transactions:
            for t in transactions:
                st.write(f"Tipo: {t[2]} | Monto: ${t[3]:.2f} | Fecha: {t[4]} | Estado: {t[5]}")
        else:
            st.info("No hay transacciones registradas.")

elif choice == "Ver Balance":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión primero.")
    else:
        st.subheader("Tu Balance Actual")
        balance = get_user_balance(st.session_state['user'][0])
        st.success(f"Tu balance actual es: ${balance:.2f}")

else:
    st.info("Selecciona una opción en el menú de la izquierda para empezar.")
