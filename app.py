import subprocess
import sys

# =====================================================================
# TRUCO PARA CONFIGURACIÓN EN AUTOMÁTICO DE RENDER (EVITA MODULE NOT FOUND)
# =====================================================================
try:
    import pymysql
except ImportError:
    print("AVISO: Pymysql no detectado en el servidor. Forzando instalación...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
        import pymysql
        print("¡Pymysql instalado con éxito desde el código!")
    except Exception as e:
        print(f"Error crítico al intentar instalar pymysql por código: {e}")

# =====================================================================
# RESTO DE TU CÓDIGO NORMAL DE FLASK
# =====================================================================
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clave_secreta_ecodieta'

# CONFIGURACIÓN DE LA BASE DE DATOS BLINDADA PARA RENDER
def obtener_conexion():
    try:
        return pymysql.connect(
            host='localhost',       # Funciona en tu PC, pero fallará en Render sin el try/except
            user='root',
            password='',            # Pon aquí tu contraseña local si usas una
            database='ecodieta',    # Nombre de tu base de datos local
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        # Evita que Render se muera al arrancar si no hay MySQL local encendido
        print(f"AVISO: No se pudo conectar a la MySQL local ({e}). La app seguirá viva.")
        return None

# RUTA PRINCIPAL (INDEX)
@app.route('/')
def index():
    return render_template('index.html')

# RUTA DE REGISTRO / CÁLCULO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        consumo_carne = request.form.get('consumo_carne')
        
        if not nombre or not consumo_carne:
            flash('Por favor, llena todos los campos.', 'danger')
            return redirect(url_for('registro'))
        
        # Fórmula de ejemplo para la huella de CO2 (1kg carne = ~27kg CO2)
        co2_calculado = float(consumo_carne) * 27.0
        
        conexion = obtener_conexion()
        if conexion:
            try:
                with conexion.cursor() as cursor:
                    sql = "INSERT INTO usuarios (nombre, consumo, co2) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (nombre, consumo_carne, co2_calculado))
                conexion.commit()
                flash('¡Datos guardados con éxito en la base de datos!', 'success')
            except Exception as err:
                flash(f'Error al guardar en la base de datos: {err}', 'warning')
            finally:
                conexion.close()
        else:
            # Si no hay base de datos (como en Render), procesa en memoria para que no se caiga la experiencia
            flash(f'¡Cálculo realizado con éxito de forma local (Sin BD)! Tu huella es de {co2_calculado} kg de CO2.', 'info')
            
        return render_template('registro.html', nombre=nombre, co2=co2_calculado)
        
    return render_template('registro.html')

# INICIO DE LA APLICACIÓN
if __name__ == '__main__':
    import os
    # Render usa una variable de entorno llamada PORT, en tu PC usará el puerto 5000 por defecto
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=True)