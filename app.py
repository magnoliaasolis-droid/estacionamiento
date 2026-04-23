from flask import Flask
import mysql.connector

app = Flask(__name__)

@app.route("/")
def inicio():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Magno",
            database="ESTACIONAMIENTO"
        )

        return "Conectado a MySQL desde Render"

    except Exception as e:
        return str(e)
