from flask import Flask
import mysql.connector

app = Flask(__name__)

@app.route("/")
def inicio():
    return "Servidor activo"

@app.route("/testdb")
def testdb():
    try:
        conexion = mysql.connector.connect(
            host="shortline.proxy.rlwy.net",
            user="root",
            port="47707",
            password="fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
            database="railway"
            connection_timeout=5
        )

        return "Conectado a MySQL desde Render"

    except Exception as e:
        return str(e)
