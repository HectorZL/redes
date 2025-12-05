import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
from snmp_logic import NetworkLogic

class NetworkMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red (Estructurado)")
        self.root.geometry("650x550")
        
        # Instanciar lógica pasando el método de log seguro
        self.logic = NetworkLogic(self.log_threadsafe)

        self._init_ui()
        self.log("Interfaz iniciada.")
        
        if not self.logic.is_snmp_available():
            self.log("ALERTA: pysnmp no detectado.")

    def _init_ui(self):
        # Estilos
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', padding=6, background="#007bff", foreground="white")
        style.map('TButton', background=[('active', '#0056b3')])

        # Main Frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Inputs
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="IP:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.entry_ip = ttk.Entry(input_frame, width=15)
        self.entry_ip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_ip.insert(0, "127.0.0.1")

        ttk.Label(input_frame, text="Comunidad:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.entry_comm = ttk.Entry(input_frame, width=15)
        self.entry_comm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_comm.insert(0, "public")

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_snmp = ttk.Button(btn_frame, text="Eficiencia BW (SNMP)", command=self.on_click_snmp)
        self.btn_snmp.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.btn_ping = ttk.Button(btn_frame, text="Eficiencia Ping", command=self.on_click_ping)
        self.btn_ping.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Log Area
        ttk.Label(main_frame, text="Bitácora:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.txt_log = scrolledtext.ScrolledText(main_frame, height=20, state=tk.DISABLED, font=("Consolas", 9))
        self.txt_log.pack(expand=True, fill=tk.BOTH)

    def log(self, msg):
        """Append log to text area."""
        self.txt_log.config(state=tk.NORMAL)
        ts = time.strftime('%H:%M:%S')
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def log_threadsafe(self, msg):
        """Callback seguro para hilos."""
        self.root.after(0, self.log, msg)

    def on_click_snmp(self):
        ip = self.entry_ip.get()
        comm = self.entry_comm.get()
        if not ip: return
        self.btn_snmp.config(state=tk.DISABLED)
        
        # Mander a llamar lógica
        self.logic.run_snmp_test(ip, comm)
        
        # Reactivar botón tras unos segundos (simple timeout visual o esperar callback real)
        # Para simplificar, lo reactivamos a los 5s, o la logica podria llamar un callback "finished"
        self.root.after(5000, lambda: self.btn_snmp.config(state=tk.NORMAL))

    def on_click_ping(self):
        ip = self.entry_ip.get()
        if not ip: return
        self.btn_ping.config(state=tk.DISABLED)
        self.logic.run_ping_test(ip)
        self.root.after(5000, lambda: self.btn_ping.config(state=tk.NORMAL))
