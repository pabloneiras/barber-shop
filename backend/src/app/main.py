import sys
from pathlib import Path

# Ensure backend/src is on sys.path so app package resolves when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database_manager import DatabaseManager



def show_menu(db: DatabaseManager):
    while True:
        print("--- BARBER SHOP (CLI) ---")
        print(
            "1. Nueva cita \n 2. Ver citas del dia \n 3. Cancelar cita \n 4. Editar cita \n 5. Ver citas restantes hoy \n 6. Ver todas las citas restantes \n 7. Salir"
        )
        option = input("Opcion: ")
        if option == "7":
            db.close_connection()
            print("Hasta luego!")
            break
        try:
            logic_menu(option, db)
        except Exception as e:
            print(f"Error: {e}. Intentalo de nuevo.")


def print_appointments(rows):
    if not rows:
        print("No hay citas.")
        return
    for row in rows:
        name = row["name"] or "Sin nombre"
        service = row["service"] or "Sin servicio"
        print(
            f"  [ID {row['appointment_id']}] {row['appointment_date']} {row['appointment_time']} | {name} ({row['phone']}) | {service}"
        )


def logic_menu(option, db: DatabaseManager):

    match option:
        case "1":
            phone, name, last_name = input(
                "Introduce (separado por espacios) telefono, nombre, apellido: "
            ).split(" ")
            client_id = db.get_or_create_client(phone, name, last_name)
            appointment_date, appointment_time, service = input(
                "Introduce dia (YYYY-MM-DD), hora (HH:MM) y servicio separados por espacios: "
            ).split(" ")
            db.insert_appointment(
                client_id, appointment_date, appointment_time, service
            )
            print("Cita guardada.")

        case "2":
            print_appointments(db.get_day_appointments())

        case "3":
            print_appointments(db.get_appointments_with_client())
            appointment_id = input("ID de la cita a cancelar: ")
            deleted = db.delete_appointment(appointment_id)
            print("Cita cancelada." if deleted else "No se encontro esa cita.")

        case "4":
            print_appointments(db.get_appointments_with_client())
            appointment_id = input("ID de la cita a editar: ")
            date = (
                input("Nueva fecha (YYYY-MM-DD) o Enter para no cambiar: ").strip()
                or None
            )
            time = input("Nueva hora (HH:MM) o Enter para no cambiar: ").strip() or None
            service = input("Nuevo servicio o Enter para no cambiar: ").strip() or None
            updated = db.update_appointment(appointment_id, date, time, service)
            print(
                "Cita actualizada."
                if updated
                else "No se encontro esa cita o no hubo cambios."
            )

        case "5":
            print_appointments(db.get_appointments_left_today())

        case "6":
            print_appointments(db.get_all_appointments_left())

        case _:
            print("Opcion no valida. Elige entre 1 y 7.")


def main():
    db = DatabaseManager(Path() / "barber_shop.db")
    db.connect()
    db.create_tables()
    show_menu(db)


if __name__ == "__main__":
    main()
