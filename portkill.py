import subprocess

def kill_port(port):
    try:
        # Portu istifadə edən PID-i tap
        result = subprocess.check_output(
            f"lsof -t -i:{port}", shell=True
        ).decode().strip()

        if not result:
            print(f"{port} portunda çalışan proses tapılmadı.")
            return

        print(f"{port} portunda çalışan PID: {result}")

        # Prosesi öldür
        subprocess.call(f"kill -9 {result}", shell=True)
        print("Proses uğurla öldürüldü.")

    except Exception as e:
        print("Xəta:", e)

# İstifadə:
kill_port(8080)   # Flask default portu
kill_port(2086)