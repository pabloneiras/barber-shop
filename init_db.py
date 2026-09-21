import sqlite3

def init_db():
    # inicio la conexion
    conexion = sqlite3.connect("barber_shop.db")
    #creo el cursor (con el cual se ejecutan los comandos)
    cursor = conexion.cursor()

    #AHORA CREO LA TABLA
    # el funcionamiento del execute es enviarle cosas en sql puro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes(
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono TEXT NOT NULL UNIQUE,
    nombre TEXT,
    apellido TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS citas(
    id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    servicio TEXT,
    recordatorio_enviado INTEGER DEFAULT 0,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente))
    """)

    conexion.commit()
    conexion.close()
    print("Base de datos creada: barber_shop.db")

if __name__ == "__main__":
    init_db()