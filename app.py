"""
CONTROL DE TEMPERATURA - APP WEB CON FLASK
============================================================
Esta es la version REAL y funcional del ejemplo. A diferencia de la
demo visual, esto corre un servidor Python de verdad: guarda los datos
en una base de datos (SQLite, un archivo local, sin instalar nada
aparte) y cualquier celular en la misma red WiFi puede usarla desde
su navegador.

Como correrla:
    1. pip install flask
    2. python app.py
    3. En la PC, anotar la IP local (Windows: ipconfig | Mac/Linux: ifconfig)
    4. Desde el celular (misma WiFi), entrar a: http://TU_IP_LOCAL:5000
"""

import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_PATH = "control_temperatura.db"

# Rango normado (cadena de frio). Ajustar segun tu caso real.
LIMITE_MIN = 2.0
LIMITE_MAX = 8.0


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea la tabla si todavia no existe (se corre una sola vez al iniciar)."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mediciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linea TEXT NOT NULL,
            temperatura REAL NOT NULL,
            operario TEXT NOT NULL,
            fecha_hora TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def evaluar_estado(temp):
    if temp < LIMITE_MIN or temp > LIMITE_MAX:
        return "Fuera de norma"
    margen = 1.0
    if temp < LIMITE_MIN + margen or temp > LIMITE_MAX - margen:
        return "Cerca del limite"
    return "OK"


@app.route("/", methods=["GET", "POST"])
def registrar():
    """Pagina principal: formulario para cargar una medicion nueva."""
    if request.method == "POST":
        linea = request.form["linea"]
        temperatura = float(request.form["temperatura"])
        operario = request.form["operario"]
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = get_db()
        conn.execute(
            "INSERT INTO mediciones (linea, temperatura, operario, fecha_hora) VALUES (?, ?, ?, ?)",
            (linea, temperatura, operario, fecha_hora),
        )
        conn.commit()
        conn.close()

        # Despues de guardar, redirige al dashboard para ver el resultado
        return redirect(url_for("dashboard"))

    return render_template("registrar.html")


@app.route("/dashboard")
def dashboard():
    """Panel con las mediciones recientes y el resumen del dia."""
    conn = get_db()
    filas = conn.execute(
        "SELECT * FROM mediciones ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    mediciones = []
    ok_count = 0
    alerta_count = 0
    for f in filas:
        estado = evaluar_estado(f["temperatura"])
        if estado == "OK":
            ok_count += 1
        if estado == "Fuera de norma":
            alerta_count += 1
        mediciones.append({
            "linea": f["linea"],
            "temperatura": f["temperatura"],
            "operario": f["operario"],
            "fecha_hora": f["fecha_hora"],
            "estado": estado,
        })

    total = len(mediciones)
    porcentaje_ok = round((ok_count / total) * 100) if total else 0

    return render_template(
        "dashboard.html",
        mediciones=mediciones,
        total=total,
        porcentaje_ok=porcentaje_ok,
        alerta_count=alerta_count,
    )


if __name__ == "__main__":
    init_db()
    # host="0.0.0.0" es lo que permite que OTROS dispositivos en la misma
    # red WiFi (como tu celular) puedan acceder, no solo la propia PC.
    app.run(host="0.0.0.0", port=5000, debug=True)
