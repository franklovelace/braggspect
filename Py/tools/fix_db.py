import sqlite3

def patch_database():
    conn = sqlite3.connect("HanawaltIndex.db")
    cursor = conn.cursor()
    try:
        print("Añadiendo columna 'name' a la tabla 'materials'...")
        cursor.execute("ALTER TABLE materials ADD COLUMN name TEXT")
        conn.commit()
        print("¡Columna añadida con éxito!")
    except sqlite3.OperationalError:
        print("La columna ya existe o hubo un error.")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()