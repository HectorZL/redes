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
        print(f"[AgentManager] Iniciando agente SNMP en el puerto {self.port}...")
        
        # Comando para iniciar snmpsimd
        # --agent-udpv4-endpoint=127.0.0.1:PORT
        command = [
            'snmpsimd', 
            f'--agent-udpv4-endpoint=127.0.0.1:{self.port}',
            # '--process-user=nobody', '--process-group=nogroup' # Usualmente para Linux, en Windows se ignora o falla
        ]
        
        # En Windows, usamos CREATE_NO_WINDOW para que no salte una ventana negra molesta
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
            # Darle un momento para arrancar y chequear si falló inmediatamente
            time.sleep(1)
            if self.process.poll() is not None:
                # Si poll() retorna algo, es que ya terminó (falló)
                _, stderr = self.process.communicate()
                print(f"[AgentManager] Error al iniciar agente: {stderr.decode('utf-8', errors='ignore')}")
                return False
            
            print(f"[AgentManager] Agente iniciado con PID: {self.process.pid}")
            return True
        except FileNotFoundError:
            print("[AgentManager] Error: No se encontró el comando 'snmpsimd'. Asegúrate de que esté instalado (pip install snmpsim).")
            return False
        except Exception as e:
            print(f"[AgentManager] Excepción al iniciar: {e}")
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
