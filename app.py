from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

MAX_AUTOS = 20
estado = True

# ------------------------
# MYSQL RAILWAY
# ------------------------
DB = {
    "host": "shortline.proxy.rlwy.net",
    "port": 47707,
    "user": "root",
    "password": "fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
    "database": "railway"
}

# ------------------------
# CONSULTAS MYSQL
# ------------------------
def query(sql, valores=None):
    con = mysql.connector.connect(**DB)
    cur = con.cursor(dictionary=True)

    if valores:
        cur.execute(sql, valores)
    else:
        cur.execute(sql)

    try:
        data = cur.fetchall()
    except:
        data = None

    con.commit()
    cur.close()
    con.close()

    return data


# ------------------------
# AUTOS ACTUALES
# SOLO DESDE ÚLTIMO RESET
# ------------------------
def autos_actuales():

    filas = query("""
        SELECT tipo
        FROM registros
        WHERE id >= (
            SELECT IFNULL(MAX(id),0)
            FROM registros
            WHERE tipo='reset_actuales'
        )
        ORDER BY id
    """)

    total = 0

    for f in filas:

        tipo = str(f["tipo"]).strip().lower()

        if tipo == "entrada":
            total += 1

        elif tipo == "salida":
            total -= 1

    return max(total, 0)


# ------------------------
# AUTOS DEL DÍA
# ------------------------
def autos_dia():
    r = query("""
        SELECT autos
        FROM registros
        ORDER BY id DESC
        LIMIT 1
    """)

    if r:
        return r[0]["autos"]
    return 0


# ------------------------
# GUARDAR EVENTO
# ------------------------
def guardar(tipo, entrada, salida, autos):

    query("""
        INSERT INTO registros
        (tipo, fecha, distancia_entrada, distancia_salida, autos)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        tipo,
        datetime.now(),
        entrada,
        salida,
        autos
    ))


# ------------------------
# API ESP32
# ------------------------
@app.route("/sensor", methods=["POST"])
def sensor():

    global estado

    if not estado:
        return jsonify({"accion": "cerrado"})

    data = request.json

    tipo = data["tipo"]
    distancia = data["distancia"]

    actuales = autos_actuales()
    dia = autos_dia()

    # ENTRADA
    if tipo == "entrada":

        if actuales >= MAX_AUTOS:
            return jsonify({"accion": "lleno"})

        guardar("entrada", distancia, 0, dia + 1)

        return jsonify({"accion": "abrir"})

    # SALIDA
    if tipo == "salida":

        if actuales <= 0:
            return jsonify({"accion": "vacio"})

        guardar("salida", 0, distancia, dia)

        return jsonify({"accion": "abrir"})

    return jsonify({"accion": "error"})


# ------------------------
# BOTONES
# ------------------------
@app.route("/abrir")
def abrir():
    global estado
    estado = True
    return "Estacionamiento abierto"


@app.route("/cerrar")
def cerrar():
    global estado
    estado = False
    return "Estacionamiento cerrado"


@app.route("/reiniciar_dia")
def reiniciar_dia():

    guardar("reinicio_dia", 0, 0, 0)

    return "Autos del día reiniciados"


@app.route("/reiniciar_actuales")
def reiniciar_actuales():

    guardar("reset_actuales", 0, 0, autos_dia())

    return "Autos actuales reiniciados"


# ------------------------
# PANEL WEB
# ------------------------
@app.route("/")
def panel():

    actuales = autos_actuales()
    dia = autos_dia()

    buscar = request.args.get("buscar")

    if buscar:
        datos = query("""
            SELECT *
            FROM registros
            WHERE id LIKE %s
            OR tipo LIKE %s
            OR fecha LIKE %s
            ORDER BY id DESC
        """, (
            "%" + buscar + "%",
            "%" + buscar + "%",
            "%" + buscar + "%"
        ))
    else:
        datos = query("""
            SELECT *
            FROM registros
            ORDER BY id DESC
            LIMIT 50
        """)

    html = f"""
    <html>
    <head>
        <title>Estacionamiento</title>

        <style>
            body {{
                font-family: Arial;
                background: #f4f4f4;
                padding: 20px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: center;
            }}

            th {{
                background: black;
                color: white;
            }}

            button {{
                padding: 10px;
                margin: 5px;
            }}

            input {{
                padding: 8px;
            }}
        </style>
    </head>

    <body>

    <h1>Estacionamiento Inteligente</h1>

    <button onclick="location.reload()">Actualizar</button>

    <br><br>

    Estado: {"ABIERTO" if estado else "CERRADO"} <br>
    Autos actuales: {actuales}/{MAX_AUTOS} <br>
    Autos del día: {dia}

    <br><br>

    <a href="/abrir"><button>Abrir</button></a>
    <a href="/cerrar"><button>Cerrar</button></a>
    <a href="/reiniciar_dia"><button>Reiniciar día</button></a>
    <a href="/reiniciar_actuales"><button>Reiniciar actuales</button></a>

    <br><br>

    <form>
        <input name="buscar" placeholder="Buscar por ID, fecha o tipo">
        <button>Buscar</button>
    </form>

    <br><br>

    <table>
        <tr>
            <th>ID</th>
            <th>Tipo</th>
            <th>Fecha</th>
            <th>Entrada</th>
            <th>Salida</th>
            <th>Autos día</th>
        </tr>
    """

    for d in datos:

        fecha_mexico = d["fecha"] - timedelta(hours=6)

        html += f"""
        <tr>
            <td>{d['id']}</td>
            <td>{d['tipo']}</td>
            <td>{fecha_mexico}</td>
            <td>{d['distancia_entrada']}</td>
            <td>{d['distancia_salida']}</td>
            <td>{d['autos']}</td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run()
