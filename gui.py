import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
import threading
from snmp_logic import NetworkLogic
import scanner

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
        # ... (keep styles)
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Inputs
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="IP:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Combobox en lugar de Entry simple
        self.combo_ip = ttk.Combobox(input_frame, width=20)
        self.combo_ip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.combo_ip.set("127.0.0.1:16161")
        self.combo_ip['values'] = ["127.0.0.1:16161"]

        # Botón Escanear pequeño al lado del combo
        self.btn_scan = ttk.Button(input_frame, text="🔍", width=3, command=self._start_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=2)

        ttk.Label(input_frame, text="Comunidad:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.entry_comm = ttk.Entry(input_frame, width=15)
        self.entry_comm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_comm.insert(0, "public")

        # Control para número de agentes
        ttk.Label(input_frame, text="Agentes:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.spin_agents = ttk.Spinbox(input_frame, from_=1, to=10, width=5)
        self.spin_agents.pack(side=tk.LEFT, padx=5)
        self.spin_agents.set(3)  # Valor por defecto: 3 agentes

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_snmp = ttk.Button(btn_frame, text="Monitoreo SNMP", command=self.on_click_snmp)
        self.btn_snmp.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.btn_rmon = ttk.Button(btn_frame, text="Monitoreo RMON", command=self.on_click_rmon)
        self.btn_rmon.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

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

    def _start_scan(self):
        """Inicia el escaneo en un hilo."""
        self.btn_scan.config(state=tk.DISABLED)
        self.log("Iniciando escaneo de red...")
        t = threading.Thread(target=scanner.scan_network_subnet, 
                             args=(self._on_ip_found, self._on_scan_finish), 
                             daemon=True)
        t.start()

    def _on_ip_found(self, ip):
        # Opcional: Loguear cada IP encontrada, o solo esperar al final
        # self.log_threadsafe(f"Host encontrado: {ip}")
        pass

    def _on_scan_finish(self, ips):
        self.root.after(0, lambda: self._update_combo(ips))

    def _update_combo(self, ips):
        self.log(f"Escaneo finalizado. Hosts encontrados: {len(ips)}")
        current = self.combo_ip.get()
        self.combo_ip['values'] = ips
        if current not in ips and ips:
            # Mantener actual si existe, o poner el primero de la lista
            pass 
        self.btn_scan.config(state=tk.NORMAL)

    def on_click_snmp(self):
        ip = self.combo_ip.get() # Obtener del combo
        comm = self.entry_comm.get()
        num_agents = int(self.spin_agents.get())
        if not ip: return
        self.btn_snmp.config(state=tk.DISABLED)
        
        self.logic.run_snmp_test(ip, comm, num_agents)
        self.root.after(5000, lambda: self.btn_snmp.config(state=tk.NORMAL))

    def on_click_ping(self):
        ip = self.combo_ip.get() # Obtener del combo
        if not ip: return
        self.btn_ping.config(state=tk.DISABLED)
        self.logic.run_ping_test(ip)
        self.root.after(5000, lambda: self.btn_ping.config(state=tk.NORMAL))

    def on_click_rmon(self):
        ip = self.combo_ip.get() # Obtener del combo
        num_agents = int(self.spin_agents.get())
        if not ip: return
        self.btn_rmon.config(state=tk.DISABLED)
        self.logic.run_rmon_test(ip, num_agents)
        self.root.after(8000, lambda: self.btn_rmon.config(state=tk.NORMAL))
