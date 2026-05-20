from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql

app = Flask(__name__)
app.secret_key = 'clave_secreta_ecodieta'

# CONFIGURACIÓN DE LA BASE DE DATOS BLINDADA PARA RENDER
def obtener_conexion():
    try:
        return pymysql.connect(
            host='localhost',       # Esto funciona en tu PC, pero fallaría en Render sin el try/except
            user='root',
            password='',            # Pon aquí tu contraseña si usas una en local
            database='ecodieta',    # Asegúrate de que coincida con el nombre de tu base de datos
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        # Si está en Render y no detecta el localhost, esto evita que el servidor se caiga (status 1)
        print(f"AVISO: No se pudo conectar a la MySQL local ({e}). La app seguirá corriendo.")
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
        
        # Validación básica
        if not nombre or not consumo_carne:
            flash('Por favor, llena todos los campos.', 'danger')
            return redirect(url_for('registro'))
        
        # Cálculo rápido de huella de CO2 (Ajusta la fórmula según tu lógica del proyecto)
        # Ejemplo: 1kg de carne equivale aprox a 27kg de CO2
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
            # Si no hay base de datos (como en Render), procesa el resultado en memoria para que el usuario lo vea
            flash(f'¡Cálculo realizado con éxito de forma local (Sin BD)! Tu huella es de {co2_calculado} kg de CO2.', 'info')
            
        return render_template('registro.html', nombre=nombre, co2=co2_calculado)
        
    return render_template('registro.html')

# INICIO DE LA APLICACIÓN
if __name__ == '__main__':
    # Usar el puerto que Render requiere por defecto, o el 5000 en tu computadora
    import os
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=True)