from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

# Datos Railway
DB_CONFIG = {
    "host": "shortline.proxy.rlwy.net",
    "port": 47707,
    "user": "root",
    "password": "fHLnKJtzHfArjeDLubPQmnntlJrTOTYt",
    "database": "railway"
}

@app.route("/")
def inicio():
    return "Servidor activo"

@app.route("/testdb")
def testdb():
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        conexion.close()
        return "Conectado a Railway"
    except Exception as e:
        return str(e)

@app.route("/ver")
def ver():
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM registro")
        datos = cursor.fetchall()

        cursor.close()
        conexion.close()

        return jsonify(datos)

    except Exception as e:
        return str(e)
