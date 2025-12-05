import subprocess
import time
import os
import signal
import sys

class SNMPAgentManager:
    """
    Administra el ciclo de vida del agente simulado 'snmpsimd'.
    Se encarga de iniciarlo en un subproceso y cerrarlo al salir.
    """
    def __init__(self, port=161, community='public'):
        self.port = port
        self.community = community
        self.process = None

    def start_agent(self):
        """Intenta iniciar snmpsimd en segundo plano."""
        print(f"[AgentManager] Buscando snmpsimd...")
        
        executable = self._find_executable()
        if not executable:
            print("[AgentManager] Error CRÍTICO: No se encontró 'snmpsimd.exe' en las rutas de Python.")
            print("Intenta reinstalar: pip install snmpsim")
            return False

        print(f"[AgentManager] Iniciando agente SNMP ({executable}) en puerto {self.port}...")
        
        # Comando para iniciar snmpsimd
        # --agent-udpv4-endpoint=127.0.0.1:PORT
        command = [
            executable, 
            f'--agent-udpv4-endpoint=127.0.0.1:{self.port}'
            # '--process-user=nobody', '--process-group=nogroup' # Ignorado en Windows
        ]
        
        # En Windows, usamos CREATE_NO_WINDOW
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            # Darle un momento para arrancar
            time.sleep(2)
            if self.process.poll() is not None:
                # Falló inmediatamente
                _, stderr = self.process.communicate()
                err_msg = stderr.decode('utf-8', errors='ignore')
                print(f"[AgentManager] El proceso falló al iniciar: {err_msg}")
                if "Access is denied" in err_msg or "Permission denied" in err_msg:
                     print("[AgentManager] SUGERENCIA: El puerto 161 requiere ADMINISTRADOR. Usa otro puerto (ej. 16161) o ejecuta como Admin.")
                return False
            
            print(f"[AgentManager] Agente iniciado con PID: {self.process.pid}")
            return True
        except Exception as e:
            print(f"[AgentManager] Excepción al iniciar: {e}")
            return False

    def _find_executable(self):
        """Busca el ejecutable snmpsimd en rutas comunes y relativas a la instalación."""
        # 1. Nombres posibles del ejecutable
        names = ['snmpsimd.exe', 'snmpsimd', 'snmpsim-command-responder.exe']
        
        # 2. Rutas candidatas
        search_paths = []
        
        # A. Ruta del Python actual (sys.executable) -> Scripts
        #   c:\blah\python.exe -> c:\blah\Scripts
        python_dir = os.path.dirname(sys.executable)
        search_paths.append(os.path.join(python_dir, 'Scripts'))
        search_paths.append(python_dir) # A veces en root (raro)

        # B. Rutas de usuario (AppData/Roaming...)
        #   Intentamos deducir de site-packages si es install --user
        import site
        try:
            # site.getusersitepackages() -> .../site-packages
            # Scripts suele estar en .../PythonXX/Scripts (un nivel arriba de Lib/site-packages?)
            # Ej: .../Python311/site-packages -> .../Python311/Scripts
            user_site = site.getusersitepackages()
            # Subir hasta encontrar carpeta padre de Lib o similar
            # Normal: .../PythonXY/site-packages (no, it is usually .../PythonXY/Lib/site-packages or similar)
            # En Windows user: AppData/Roaming/Python/Python311/site-packages
            # Scripts está en AppData/Roaming/Python/Python311/Scripts
            search_paths.append(os.path.join(os.path.dirname(user_site), 'Scripts'))
            
            # Alternative: site.getuserbase() -> AppData/Roaming/Python/Python311
            user_base = site.getuserbase()
            search_paths.append(os.path.join(user_base, 'Scripts'))
        except:
            pass
        
        # C. PATH del sistema
        path_env = os.environ.get('PATH', '').split(os.pathsep)
        search_paths.extend(path_env)

        # 3. Búsqueda
        for path in search_paths:
            if not path or not os.path.isdir(path): continue
            for name in names:
                full_path = os.path.join(path, name)
                if os.path.isfile(full_path):
                    return full_path
        
        # 4. Intento final con shutil.which por si acaso está en PATH global bien definido
        import shutil
        for name in names:
            res = shutil.which(name)
            if res: return res

        return None

    def stop_agent(self):
        """Detiene el agente si está corriendo."""
        if self.process:
            print(f"[AgentManager] Deteniendo agente (PID {self.process.pid})...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("[AgentManager] Agente detenido.")
            self.process = None
