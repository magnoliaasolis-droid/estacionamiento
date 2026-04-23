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
            port=47707,
            user="root",
            password="fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
            database="railway",
            connection_timeout=5
        )
        return "Conectado a Railway"
    except Exception as e:
        return str(e)
