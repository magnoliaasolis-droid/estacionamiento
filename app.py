from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

MAX_AUTOS = 20
estado = True

DB = {
    "host":"shortline.proxy.rlwy.net",
    "port":47707,
    "user":"root",
    "password":"fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
    "database":"railway"
}

# ========================
def query(sql,val=None):
    con=mysql.connector.connect(**DB)
    cur=con.cursor(dictionary=True)

    if val:
        cur.execute(sql,val)
    else:
        cur.execute(sql)

    try:
        data=cur.fetchall()
    except:
        data=None

    con.commit()
    cur.close()
    con.close()

    return data

# ========================
def autos_actuales():

    filas=query("SELECT tipo FROM registros ORDER BY id")

    t=0
    for f in filas:
        if f["tipo"]=="entrada": t+=1
        elif f["tipo"]=="salida": t-=1
        elif f["tipo"]=="reset_actuales": t=0

    return max(t,0)

# ========================
def autos_dia():
    r=query("SELECT autos FROM registros ORDER BY id DESC LIMIT 1")
    return r[0]["autos"] if r else 0

# ========================
def guardar(tipo,e,s,a):
    query("""
    INSERT INTO registros
    (tipo,fecha,distancia_entrada,distancia_salida,autos)
    VALUES(%s,%s,%s,%s,%s)
    """,(tipo,datetime.now(),e,s,a))

# ========================
@app.route("/sensor",methods=["POST"])
def sensor():

    global estado

    if not estado:
        return jsonify({"accion":"cerrado"})

    data=request.json
    tipo=data["tipo"]
    d=data["distancia"]

    actuales=autos_actuales()
    dia=autos_dia()

    if tipo=="entrada":

        if actuales>=MAX_AUTOS:
            return jsonify({"accion":"lleno"})

        guardar("entrada",d,0,dia+1)
        return jsonify({"accion":"abrir"})

    if tipo=="salida":
        guardar("salida",0,d,dia)
        return jsonify({"accion":"abrir"})

    return jsonify({"accion":"error"})

# ========================
@app.route("/abrir")
def abrir():
    global estado
    estado=True
    return "ok"

@app.route("/cerrar")
def cerrar():
    global estado
    estado=False
    return "ok"

@app.route("/reiniciar_dia")
def reiniciar_dia():
    guardar("reinicio_dia",0,0,0)
    return "ok"

@app.route("/reiniciar_actuales")
def reiniciar_actuales():
    guardar("reset_actuales",0,0,autos_dia())
    return "ok"

# ========================
@app.route("/")
def panel():

    actuales=autos_actuales()
    dia=autos_dia()

    b=request.args.get("buscar")

    if b:
        datos=query("""
        SELECT * FROM registros
        WHERE id LIKE %s OR tipo LIKE %s OR fecha LIKE %s
        ORDER BY id DESC
        """,("%"+b+"%","%"+b+"%","%"+b+"%"))
    else:
        datos=query("SELECT * FROM registros ORDER BY id DESC LIMIT 50")

    html=f"""
    <html>
    <head>
    <title>Estacionamiento</title>

    <style>
    body {{font-family:Arial;background:#f4f4f4;padding:20px}}
    table {{background:white;border-collapse:collapse;width:100%}}
    th,td {{padding:10px;border:1px solid #ddd;text-align:center}}
    th {{background:#222;color:white}}
    button {{padding:8px 15px;margin:5px}}
    input {{padding:8px}}
    </style>

    </head>

    <body>

    <h1>Estacionamiento</h1>

    <button onclick="location.reload()">Actualizar</button>

    <br><br>

    Estado: {"ABIERTO" if estado else "CERRADO"}<br>
    Autos actuales: {actuales}/{MAX_AUTOS}<br>
    Autos dia: {dia}<br><br>

    <a href=/abrir><button>Abrir</button></a>
    <a href=/cerrar><button>Cerrar</button></a>
    <a href=/reiniciar_dia><button>Reiniciar dia</button></a>
    <a href=/reiniciar_actuales><button>Reiniciar actuales</button></a>

    <br><br>

    <form>
    <input name=buscar placeholder="Buscar">
    <button>Buscar</button>
    </form>

    <br>

    <table>
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

        f=d["fecha"]-timedelta(hours=6)

        html+=f"""
        <tr>
        <td>{d['id']}</td>
        <td>{d['tipo']}</td>
        <td>{f}</td>
        <td>{d['distancia_entrada']}</td>
        <td>{d['distancia_salida']}</td>
        <td>{d['autos']}</td>
        </tr>
        """

    html+="</table></body></html>"

    return html

if __name__=="__main__":
    app.run()
