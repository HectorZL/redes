import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
import threading
from snmp_logic import NetworkLogic
from data_export import DataExporter
from visualizer import DataVisualizer
from threshold_config import ThresholdConfigDialog
import scanner

class NetworkMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red Avanzado (SNMP/RMON)")
        self.root.geometry("750x650")
        
        # Instanciar lógica y módulos
        self.logic = NetworkLogic(self.log_threadsafe)
        self.exporter = DataExporter()
        self.visualizer = DataVisualizer()
        
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

        # === INPUT FRAME ===
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="IP:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Combobox para IP
        self.combo_ip = ttk.Combobox(input_frame, width=20)
        self.combo_ip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.combo_ip.set("127.0.0.1:16161")
        self.combo_ip['values'] = ["127.0.0.1:16161"]

        # Botón Escanear
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
        self.spin_agents.set(3)

        # === BOTONES DE MONITOREO ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_snmp = ttk.Button(btn_frame, text="Monitoreo SNMP", command=self.on_click_snmp)
        self.btn_snmp.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.btn_rmon = ttk.Button(btn_frame, text="Monitoreo RMON", command=self.on_click_rmon)
        self.btn_rmon.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.btn_ping = ttk.Button(btn_frame, text="Eficiencia Ping", command=self.on_click_ping)
        self.btn_ping.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # === FRAME DE EXPORTACIÓN Y VISUALIZACIÓN ===
        tools_frame = ttk.LabelFrame(main_frame, text="📊 Herramientas Avanzadas", padding="10")
        tools_frame.pack(fill=tk.X, pady=10)

        # Fila 1: Exportación
        export_row = ttk.Frame(tools_frame)
        export_row.pack(fill=tk.X, pady=5)

        ttk.Label(export_row, text="Exportar:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.btn_export_csv = ttk.Button(export_row, text="📄 CSV", width=12, command=self.export_csv)
        self.btn_export_csv.pack(side=tk.LEFT, padx=2)

        self.btn_export_json = ttk.Button(export_row, text="📋 JSON", width=12, command=self.export_json)
        self.btn_export_json.pack(side=tk.LEFT, padx=2)

        # Fila 2: Visualización
        viz_row = ttk.Frame(tools_frame)
        viz_row.pack(fill=tk.X, pady=5)

        ttk.Label(viz_row, text="Visualizar:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.btn_graph = ttk.Button(viz_row, text="📈 Gráfico Temporal", width=18, command=self.show_graph)
        self.btn_graph.pack(side=tk.LEFT, padx=2)

        self.btn_distribution = ttk.Button(viz_row, text="📊 Distribución", width=18, command=self.show_distribution)
        self.btn_distribution.pack(side=tk.LEFT, padx=2)

        # Fila 3: Comparación y Configuración
        config_row = ttk.Frame(tools_frame)
        config_row.pack(fill=tk.X, pady=5)

        ttk.Label(config_row, text="Análisis:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.btn_compare = ttk.Button(config_row, text="⚖️ SNMP vs RMON", width=18, command=self.show_comparison)
        self.btn_compare.pack(side=tk.LEFT, padx=2)

        self.btn_config = ttk.Button(config_row, text="⚙️ Config. Umbrales", width=18, command=self.config_thresholds)
        self.btn_config.pack(side=tk.LEFT, padx=2)

        # === LOG ÁREA ===
        ttk.Label(main_frame, text="📝 Bitácora:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.txt_log = scrolledtext.ScrolledText(main_frame, height=18, state=tk.DISABLED, font=("Consolas", 9))
        self.txt_log.pack(expand=True, fill=tk.BOTH)

        # === STATUS BAR ===
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="✓ Listo", foreground="green", font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT)

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

    def update_status(self, msg, color="green"):
        """Actualiza la barra de estado."""
        self.status_label.config(text=msg, foreground=color)

    # === MÉTODOS DE SCAN ===
    def _start_scan(self):
        """Inicia el escaneo en un hilo."""
        self.btn_scan.config(state=tk.DISABLED)
        self.log("Iniciando escaneo de red...")
        self.update_status("🔍 Escaneando...", "orange")
        t = threading.Thread(target=scanner.scan_network_subnet, 
                             args=(self._on_ip_found, self._on_scan_finish), 
                             daemon=True)
        t.start()

    def _on_ip_found(self, ip):
        pass

    def _on_scan_finish(self, ips):
        self.root.after(0, lambda: self._update_combo(ips))

    def _update_combo(self, ips):
        self.log(f"Escaneo finalizado. Hosts encontrados: {len(ips)}")
        self.combo_ip['values'] = ips
        self.btn_scan.config(state=tk.NORMAL)
        self.update_status("✓ Listo")

    # === MÉTODOS DE MONITOREO ===
    def on_click_snmp(self):
        ip = self.combo_ip.get()
        comm = self.entry_comm.get()
        num_agents = int(self.spin_agents.get())
        if not ip: return
        self.btn_snmp.config(state=tk.DISABLED)
        self.update_status("🔄 Ejecutando SNMP...", "blue")
        
        self.logic.run_snmp_test(ip, comm, num_agents)
        self.root.after(5000, lambda: [
            self.btn_snmp.config(state=tk.NORMAL),
            self.update_status("✓ Listo")
        ])

    def on_click_ping(self):
        ip = self.combo_ip.get()
        if not ip: return
        self.btn_ping.config(state=tk.DISABLED)
        self.update_status("🔄 Ejecutando Ping...", "blue")
        self.logic.run_ping_test(ip)
        self.root.after(5000, lambda: [
            self.btn_ping.config(state=tk.NORMAL),
            self.update_status("✓ Listo")
        ])

    def on_click_rmon(self):
        ip = self.combo_ip.get()
        num_agents = int(self.spin_agents.get())
        if not ip: return
        self.btn_rmon.config(state=tk.DISABLED)
        self.update_status("🔄 Ejecutando RMON...", "blue")
        self.logic.run_rmon_test(ip, num_agents)
        self.root.after(8000, lambda: [
            self.btn_rmon.config(state=tk.NORMAL),
            self.update_status("✓ Listo")
        ])

    # === MÉTODOS DE EXPORTACIÓN ===
    def export_csv(self):
        """Exporta los últimos datos a CSV."""
        try:
            if not self.logic.last_snmp_data and not self.logic.last_rmon_data:
                messagebox.showwarning("Sin Datos", 
                    "No hay datos para exportar.\nEjecuta primero una medición SNMP o RMON.")
                return
            
            files = []
            
            if self.logic.last_snmp_data:
                filename = self.exporter.export_snmp_to_csv(
                    self.logic.last_snmp_data, 
                    len(self.logic.last_snmp_data)
                )
                files.append(filename)
                self.log(f"SNMP exportado a: {filename}")
            
            if self.logic.last_rmon_data:
                filename = self.exporter.export_rmon_to_csv(
                    self.logic.last_rmon_data,
                    self.logic.last_rmon_data.get('num_agents', 1)
                )
                files.append(filename)
                self.log(f"RMON exportado a: {filename}")
            
            msgbox_text = "✓ Datos exportados exitosamente a CSV:\n\n" + "\n".join(files)
            messagebox.showinfo("Exportación Exitosa", msgbox_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar CSV: {e}")

    def export_json(self):
        """Exporta los últimos datos a JSON."""
        try:
            if not self.logic.last_snmp_data and not self.logic.last_rmon_data:
                messagebox.showwarning("Sin Datos", 
                    "No hay datos para exportar.\nEjecuta primero una medición SNMP o RMON.")
                return
            
            files = []
            
            if self.logic.last_snmp_data:
                filename = self.exporter.export_snmp_to_json(
                    self.logic.last_snmp_data,
                    len(self.logic.last_snmp_data)
                )
                files.append(filename)
                self.log(f"SNMP exportado a: {filename}")
            
            if self.logic.last_rmon_data:
                filename = self.exporter.export_rmon_to_json(
                    self.logic.last_rmon_data,
                    self.logic.last_rmon_data.get('num_agents', 1)
                )
                files.append(filename)
                self.log(f"RMON exportado a: {filename}")
            
            msgbox_text = "✓ Datos exportados exitosamente a JSON:\n\n" + "\n".join(files)
            messagebox.showinfo("Exportación Exitosa", msgbox_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar JSON: {e}")

    # === MÉTODOS DE VISUALIZACIÓN ===
    def show_graph(self):
        """Muestra gráfico de utilización temporal."""
        try:
            if not self.logic.last_rmon_data or not self.logic.last_rmon_data.get('history'):
                messagebox.showwarning("Sin Datos", 
                    "No hay datos de historial RMON.\nEjecuta primero una medición RMON.")
                return
            
            self.visualizer.plot_utilization_history(
                self.logic.last_rmon_data['history'],
                self.root
            )
            self.log("Gráfico de utilización mostrado.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar gráfico: {e}")

    def show_distribution(self):
        """Muestra gráfico de distribución de paquetes."""
        try:
            if not self.logic.last_rmon_data or not self.logic.last_rmon_data.get('agents'):
                messagebox.showwarning("Sin Datos", 
                    "No hay datos RMON.\nEjecuta primero una medición RMON.")
                return
            
            self.visualizer.plot_packet_distribution(
                self.logic.last_rmon_data,
                self.root
            )
            self.log("Gráfico de distribución mostrado.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar distribución: {e}")

    def show_comparison(self):
        """Muestra tabla comparativa SNMP vs RMON."""
        try:
            self.visualizer.show_comparison_table(self.root)
            self.log("Tabla comparativa SNMP vs RMON mostrada.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar comparación: {e}")

    def config_thresholds(self):
        """Abre diálogo de configuración de umbrales."""
        try:
            def on_threshold_update(new_thresholds):
                self.logic.update_alarm_thresholds(new_thresholds)
                self.log(f"Umbrales actualizados: {new_thresholds}")
            
            ThresholdConfigDialog(
                self.root,
                self.logic.alarm_thresholds,
                on_threshold_update
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir configuración: {e}")
