from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

MAX_AUTOS = 20
estado_estacionamiento = True

DB_CONFIG = {
    "host": "shortline.proxy.rlwy.net",
    "port": 47707,
    "user": "root",
    "password": "fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
    "database": "railway"
}

# =============================
# AUTOS ACTUALES (entrada-salida)
# =============================
def obtener_autos_actuales():

    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
        SUM(CASE WHEN tipo='entrada' THEN 1 ELSE 0 END) -
        SUM(CASE WHEN tipo='salida' THEN 1 ELSE 0 END)
        FROM registros
    """)

    row = cursor.fetchone()

    cursor.close()
    conexion.close()

    if row[0] is None:
        return 0

    return row[0]


# =============================
# AUTOS DEL DIA (columna autos)
# =============================
def obtener_autos_dia():

    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT autos 
        FROM registros 
        ORDER BY id DESC 
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conexion.close()

    if row:
        return row[0]
    else:
        return 0


# =============================
# GUARDAR EVENTO
# =============================
def guardar_evento(tipo, d1, d2, autos_dia):

    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    fecha = datetime.now()

    sql = """
    INSERT INTO registros
    (tipo, fecha, distancia_entrada, distancia_salida, autos)
    VALUES (%s,%s,%s,%s,%s)
    """

    cursor.execute(sql,(tipo,fecha,d1,d2,autos_dia))

    conexion.commit()
    cursor.close()
    conexion.close()


# =============================
# API ESP32
# =============================
@app.route("/sensor", methods=["POST"])
def sensor():

    if not estado_estacionamiento:
        return jsonify({"accion":"cerrado"})

    autos_actuales = obtener_autos_actuales()
    autos_dia = obtener_autos_dia()

    data = request.json
    tipo = data["tipo"]
    distancia = data["distancia"]

    # ENTRADA
    if tipo == "entrada":

        if autos_actuales >= MAX_AUTOS:
            return jsonify({"accion":"lleno"})

        autos_dia += 1

        guardar_evento("entrada", distancia, 0, autos_dia)

        return jsonify({"accion":"abrir"})

    # SALIDA
    if tipo == "salida":

        guardar_evento("salida", 0, distancia, autos_dia)

        return jsonify({"accion":"abrir"})

    return jsonify({"accion":"error"})


# =============================
# CONTROLES
# =============================
@app.route("/abrir")
def abrir():
    global estado_estacionamiento
    estado_estacionamiento = True
    return "abierto"

@app.route("/cerrar")
def cerrar():
    global estado_estacionamiento
    estado_estacionamiento = False
    return "cerrado"


@app.route("/reiniciar_dia")
def reiniciar_dia():

    guardar_evento(
        "reinicio",
        0,
        0,
        0
    )

    return "reiniciado"


# =============================
# PANEL
# =============================
@app.route("/")
def panel():

    autos_actuales = obtener_autos_actuales()
    autos_dia = obtener_autos_dia()

    buscar = request.args.get("buscar")

    conexion = mysql.connector.connect(**DB_CONFIG)
    cursor = conexion.cursor(dictionary=True)

    if buscar:

        sql = """
        SELECT * FROM registros 
        WHERE 
        id LIKE %s OR
        tipo LIKE %s OR
        fecha LIKE %s OR
        autos LIKE %s
        ORDER BY id DESC
        """

        like = "%" + buscar + "%"

        cursor.execute(sql,(like,like,like,like))

    else:
        cursor.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 50")

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

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
    <h2>Autos actuales: {autos_actuales}/{MAX_AUTOS}</h2>
    <h2>Autos del dia: {autos_dia}</h2>
    <h2>{lleno}</h2>

    <br>

    <a href="/abrir">Abrir</a>
    <a href="/cerrar">Cerrar</a>
    <a href="/reiniciar_dia">Reiniciar dia</a>

    <br><br>

    <form method="GET">
    <input name="buscar" placeholder="Buscar...">
    <button>Buscar</button>
    </form>

    <br>

    <table border="1">
    <tr>
    <th>ID</th>
    <th>Tipo</th>
    <th>Fecha</th>
    <th>Entrada</th>
    <th>Salida</th>
    <th>Autos dia</th>
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
