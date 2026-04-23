from flask import Flask
import mysql.connector

app = Flask(__name__)

@app.route("/")
def inicio():
    try:
        conexion = mysql.connector.connect(
            host="shortline.proxy.rlwy.net",
            user="root",
            password="fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
            database="railway"
        )

        return "Conectado a MySQL desde Render"

    except Exception as e:
        return str(e)
