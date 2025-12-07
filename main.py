import tkinter as tk
import atexit
from gui import NetworkMonitorGUI
from agent_manager import SNMPAgentManager

def main():
    # 1. Iniciar el Agente SNMP en segundo plano (Puerto 16161 para evitar admin)
    agent = SNMPAgentManager(port=16161)
    if agent.start_agent():
        print("Agente SNMP iniciado correctamente.")
    else:
        print("ADVERTENCIA: No se pudo iniciar el agente SNMP (¿Puerto ocupado o falta permisos?).")

    # Asegurar que se cierre al salir
    atexit.register(agent.stop_agent)

    # 2. Iniciar la GUI
    root = tk.Tk()
    app = NetworkMonitorGUI(root)
    
    # Manejar cierre de ventana explícito
    def on_close():
        agent.stop_agent()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()