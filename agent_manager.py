import subprocess
import time
import os
import sys

class SNMPAgentManager:
    """
    Administra el ciclo de vida del agente simulado 'snmpsim'.
    Se encarga de iniciarlo en un subproceso y cerrarlo al salir.
    """
    def __init__(self, port=16161, community='public'):
        self.port = port
        self.community = community
        self.process = None

    def start_agent(self):
        """Intenta iniciar snmpsim responder en segundo plano."""
        print(f"[AgentManager] Iniciando agente SNMP en puerto {self.port}...")
        
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
        # Usar Python module en lugar de buscar executable
        command = [
            sys.executable,  # Usar el mismo Python que está ejecutando este script
            '-m', 'snmpsim.commands.responder',
            f'--agent-udpv4-endpoint=127.0.0.1:{self.port}',
            f'--data-dir={data_dir}'
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True  # Use text mode
            )
            # Darle un momento para arrancar
            time.sleep(2)
            if self.process.poll() is not None:
                # Falló inmediatamente
                output, _ = self.process.communicate()
                print(f"[AgentManager] El proceso falló al iniciar: {output}")
                if "Access is denied" in output or "Permission denied" in output:
                     print("[AgentManager] SUGERENCIA: El puerto 161 requiere ADMINISTRADOR. Usa otro puerto (ej. 16161) o ejecuta como Admin.")
                return False
            
            print(f"[AgentManager] Agente iniciado con PID: {self.process.pid}")
            return True
        except Exception as e:
            print(f"[AgentManager] Excepción al iniciar: {e}")
            print("[AgentManager] Asegúrate de que snmpsim esté instalado: pip install snmpsim")
            return False

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
