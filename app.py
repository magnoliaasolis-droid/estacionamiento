from flask import Flask
import mysql.connector

app = Flask(__name__)

@app.route("/")
def inicio():
    try:
        conexion = mysql.connector.connect(
            host="TU_HOST",
            user="TU_USUARIO",
            password="TU_PASSWORD",
            database="TU_DB"
        )

        return "Conectado a MySQL desde Render"

    except Exception as e:
        return str(e)
