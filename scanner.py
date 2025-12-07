import socket
import subprocess
import platform
import threading
from queue import Queue

def get_local_ip():
    """Detecta la IP local de la máquina (que sale a internet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No se conecta realmente, solo deduce la interfaz de salida
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip

def get_subnet_base(ip):
    """Devuelve la base de la subred (ej. '192.168.1.'). Asume /24."""
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}."
    return None

def ping_host(ip):
    """Hace ping a una sola IP. Retorna True si responde."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Timeout corto (-w 500ms en Windows, -W 1s en Linux/Mac)
    timeout_arg = ['-w', '500'] if platform.system().lower() == 'windows' else ['-W', '1']
    
    command = ['ping', param, '1', *timeout_arg, ip]
    
    # Ocultar ventana en Windows
    startupinfo = None
    if platform.system().lower() == 'windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    try:
        res = subprocess.run(
            command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo
        )
        return res.returncode == 0
    except Exception:
        return False

def scan_network_subnet(callback_found=None, callback_finish=None):
    """
    Escanea la subred local (254 hosts) usando hilos.
    callback_found(ip): Se llama cuando se encuentra un host.
    callback_finish(list_ips): Se llama al terminar.
    """
    local_ip = get_local_ip()
    base = get_subnet_base(local_ip)
    
    if not base or local_ip.startswith("127."):
        if callback_finish: callback_finish(["127.0.0.1"])
        return

    found_ips = []
    
    def worker(q):
        while True:
            ip = q.get()
            if ip is None: break
            if ping_host(ip):
                found_ips.append(ip)
                if callback_found: callback_found(ip)
            q.task_done()

    # Lanzar 50 hilos para que sea rápido
    queue = Queue()
    threads = []
    for _ in range(50):
        t = threading.Thread(target=worker, args=(queue,), daemon=True)
        t.start()
        threads.append(t)

    # Encolar IPs 1..254
    for i in range(1, 255):
        queue.put(f"{base}{i}")

    # Esperar
    queue.join()
    
    # Parar hilos
    for _ in range(50):
        queue.put(None)
    
    # Ordenar y añadir localhost al final si se desea
    found_ips.sort(key=lambda ip: int(ip.split('.')[-1]))
    
    # Asegurar que incluimos el localhost simulado
    if "127.0.0.1" not in found_ips:
        found_ips.insert(0, "127.0.0.1:16161")
    
    if callback_finish:
        callback_finish(found_ips)
