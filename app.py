from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# =========================
# CONFIG
# =========================
MAX_AUTOS = 20
estado_estacionamiento = False
autos_actuales = 0

DB_CONFIG = {
    "host": "shortline.proxy.rlwy.net",
    "port": 47707,
    "user": "root",
    "password": "fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
    "database": "railway"
}

# =========================
# GUARDAR EVENTO
# =========================
def guardar_evento(tipo, d1, d2):

    global autos_actuales

    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    fecha = datetime.now()

    sql = """
    INSERT INTO registros
    (tipo, fecha, distancia_entrada, distancia_salida, autos)
    VALUES (%s,%s,%s,%s,%s)
    """

    cursor.execute(sql,(tipo,fecha,d1,d2,autos_actuales))

    conexion.commit()
    cursor.close()
    conexion.close()

# =========================
# API ESP32
# =========================
@app.route("/sensor", methods=["POST"])
def sensor():

    global autos_actuales
    global estado_estacionamiento

    if not estado_estacionamiento:
        return jsonify({"accion":"cerrado"})

    data = request.json
    tipo = data["tipo"]
    distancia = data["distancia"]

    # ================= ENTRADA
    if tipo == "entrada":

        if autos_actuales >= MAX_AUTOS:
            return jsonify({"accion":"lleno"})

        autos_actuales += 1

        guardar_evento("entrada", distancia, 0)

        return jsonify({"accion":"abrir"})

    # ================= SALIDA
    if tipo == "salida":

        if autos_actuales > 0:
            autos_actuales -= 1

        guardar_evento("salida", 0, distancia)

        return jsonify({"accion":"abrir"})

    return jsonify({"accion":"error"})

# =========================
# ABRIR
# =========================
@app.route("/abrir")
def abrir():
    global estado_estacionamiento
    estado_estacionamiento = True
    return "Estacionamiento abierto"

# =========================
# CERRAR
# =========================
@app.route("/cerrar")
def cerrar():
    global estado_estacionamiento
    estado_estacionamiento = False
    return "Estacionamiento cerrado"

# =========================
# REINICIAR
# =========================
@app.route("/reiniciar")
def reiniciar():
    global autos_actuales
    autos_actuales = 0
    return "Contador reiniciado"

# =========================
# PANEL WEB
# =========================
@app.route("/")
def panel():

    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 50")
        datos = cursor.fetchall()

        cursor.close()
        conexion.close()

    except Exception as e:
        return "ERROR: " + str(e)

    estado = "ABIERTO" if estado_estacionamiento else "CERRADO"
    lleno = "LLENO" if autos_actuales >= MAX_AUTOS else "DISPONIBLE"

    html = f"""
    <html>
    <head>
    <meta http-equiv="refresh" content="3">
    <title>Estacionamiento</title>
    </head>

    <body>

    <h1>ESTACIONAMIENTO</h1>

    <h2>Estado: {estado}</h2>
    <h2>Autos: {autos_actuales}/{MAX_AUTOS}</h2>
    <h2>{lleno}</h2>

    <br>

    <a href="/abrir">ABRIR</a><br>
    <a href="/cerrar">CERRAR</a><br>
    <a href="/reiniciar">REINICIAR</a>

    <br><br>

    <table border="1">
    <tr>
    <th>ID</th>
    <th>Tipo</th>
    <th>Fecha</th>
    <th>Entrada</th>
    <th>Salida</th>
    <th>Autos</th>
    </tr>
    """

    for d in datos:
        html += f"""
        <tr>
        <td>{d['id']}</td>
        <td>{d['tipo']}</td>
        <td>{d['fecha']}</td>
        <td>{d['distancia_entrada']}</td>
        <td>{d['distancia_salida']}</td>
        <td>{d['autos']}</td>
        </tr>
        """

    html += "</table></body></html>"

    return html
