# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request
import pymysql  # Puedes usar tamién mysql.connector si lo prefieres

app = Flask(__name__)

# Configuración de los parámetros de conexión a tu Base de Datos MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # Cambia por tu usuario de MySQL
    'password': '',       # Cambia por tu contraseña de MySQL
    'database': 'eco_dieta_db',
    'port': 3306
}

def obtener_conexion():
    """Establece y retorna la conexión a la base de datos MySQL."""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        cursorclass=pymysql.cursors.DictCursor
    )


# ------------------------------------------------------------------
# RUTAS DE CONTROL DE LAS VISTAS (FRONTEND)
# ------------------------------------------------------------------

@app.route('/')
def index():
    """Ruta 1: Renderiza el Dashboard Principal (Cuestionario, Guía e Impacto)."""
    return render_template('index.html')


@app.route('/registro')
def registro():
    """Ruta 2: Renderiza la sección secundaria de Mis Retos y Calendario."""
    return render_template('registro.html')


# ------------------------------------------------------------------
# RUTA DE LA API: RECEPCIÓN Y ALMACENAMIENTO DE DATOS (BACKEND)
# ------------------------------------------------------------------

@app.route('/api/guardar-progreso', methods=['POST'])
def guardar_progreso():
    """
    API Endpoint para recibir las métricas de la huella de carbono 
    y el avance de los retos de los alumnos desde el navegador.
    """
    datos = request.get_json()
    
    if not datos:
        return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
        
    correo = datos.get('correo')
    huella_co2 = datos.get('huella_co2')
    dia_completado = datos.get('dia_completado') # Número de día del reto
    
    # Validación básica de datos obligatorios
    if not correo:
        return jsonify({"status": "error", "message": "El correo es obligatorio"}), 400

    try:
        # Abrimos la conexión a MySQL
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # 1. Insertar o actualizar los datos generales del usuario y su huella actual
            sql_usuario = """
                INSERT INTO usuarios (correo, ultima_huella) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE ultima_huella = %s
            """
            cursor.execute(sql_usuario, (correo, huella_co2, huella_co2))
            
            # 2. Si el usuario marcó una palomita en el calendario, guardamos ese día de reto
            if dia_completado is not None:
                sql_reto = """
                    INSERT IGNORE INTO progreso_retos (correo, dia_reto, completado) 
                    VALUES (%s, %s, TRUE)
                """
                cursor.execute(sql_reto, (correo, dia_completado))
                
            # Consolidamos los cambios en la BD
            conexion.commit()
            
        return jsonify({
            "status": "success", 
            "message": f"Progreso del alumno ({correo.split('@')[0]}) sincronizado con éxito."
        }), 200

    except pymysql.MySQLError as e:
        # En caso de error en la BD (ej. tabla no creada), muestra la advertencia sin tumbar la app
        print(f" ERROR DE CONEXIÓN CON MYSQL: {e}")
        return jsonify({
            "status": "offline_success", 
            "message": "Los datos se procesaron, pero la base de datos local está desconectada."
        }), 200
        
    finally:
        # Aseguramos el cierre de conexiones para evitar fugas de memoria en el servidor
        if 'conexion' in locals() and conexion.open:
            conexion.close()


# ------------------------------------------------------------------
# INICIALIZACIÓN DEL SERVIDOR FLASK
# ------------------------------------------------------------------

if __name__ == '__main__':
    # debug=True recarga el servidor automáticamente al cambiar código de Python
    # port=5000 levanta la aplicación en http://127.0.0.1:5000/
    app.run(debug=True, port=5000)