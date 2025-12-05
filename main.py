import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import time
import subprocess
import platform
import re
from threading import Timer, Thread

import asyncio

# Intenta importar pysnmp. Si no está, avisa al usuario.
try:
    # Intento de importación para versiones modernas (v7+)
    from pysnmp.hlapi.asyncio import (get_cmd, SnmpEngine, CommunityData, 
                                      UdpTransportTarget, ContextData, 
                                      ObjectType, ObjectIdentity)
    PYSNMP_AVAILABLE = True
    IS_V7 = True
except ImportError:
    try:
        # Fallback para versiones antiguas
        from pysnmp.hlapi import (getCmd, SnmpEngine, CommunityData, 
                                       UdpTransportTarget, ContextData, 
                                       ObjectType, ObjectIdentity)
        PYSNMP_AVAILABLE = True
        IS_V7 = False
    except ImportError as e:
        PYSNMP_AVAILABLE = False
        print(f"ADVERTENCIA error detallado: {e}")
        print("ADVERTENCIA: 'pysnmp' no está instalado o tiene dependencias faltantes.")
        print("Por favor, instálelo con: pip install pysnmp")


class NetworkMonitorApp:
    """
    Clase principal para la aplicación de monitoreo de red.
    Incluye pruebas de eficiencia real:
    - Bandwidth/Error Rate via SNMP (Calculado con Delta)
    - Latencia/Loss via Ping
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red (Eficiencia Real - SNMP/Ping)")
        self.root.geometry("650x550")

        # --- Estilo ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', padding=6, relief="flat", background="#007bff", foreground="white")
        style.map('TButton', background=[('active', '#0056b3')])
        style.configure('TFrame', background="#f0f0f0")
        style.configure('TLabel', background="#f0f0f0")

        # --- Marco Principal ---
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Sección de Entrada ---
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="IP Agente:", font=("Inter", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.ip_entry = ttk.Entry(input_frame, width=20, font=("Inter", 10))
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.ip_entry.insert(0, "127.0.0.1") # Apuntamos a snmpsim

        ttk.Label(input_frame, text="Comunidad:", font=("Inter", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.community_entry = ttk.Entry(input_frame, width=15, font=("Inter", 10))
        self.community_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.community_entry.insert(0, "public") # Comunidad por defecto

        # --- Sección de Botones ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.snmp_button = ttk.Button(button_frame, text="Eficiencia BW (SNMP)", command=self.query_snmp_real)
        self.snmp_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.rmon_button = ttk.Button(button_frame, text="Eficiencia Latencia (Ping)", command=self.measure_network_efficiency)
        self.rmon_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # --- Área de Salida (Log) ---
        ttk.Label(main_frame, text="Registro de Eventos:", font=("Inter", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=20, width=80, state=tk.DISABLED, font=("Courier New", 9))
        self.output_text.pack(expand=True, fill=tk.BOTH)

        self.log("Aplicación iniciada. Listo para consultas.")
        if not PYSNMP_AVAILABLE:
            self.log("ERROR: 'pysnmp' no se encontró. La consulta SNMP real está deshabilitada.")
            self.snmp_button.config(state=tk.DISABLED)
        self.log("Asegúrese de que 'snmpsim' esté corriendo en 127.0.0.1:161.")


    def log(self, message):
        """Añade un mensaje al área de texto de salida. (SOLO HILO PRINCIPAL)"""
        if not self.root.winfo_exists(): # Evita error si la ventana se cierra
            return
        self.output_text.config(state=tk.NORMAL)
        timestamp = time.strftime('%H:%M:%S')
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.output_text.see(tk.END) # Auto-scroll
        self.output_text.config(state=tk.DISABLED)

    def log_threadsafe(self, message):
        """Añade un mensaje al log de forma segura desde cualquier hilo."""
        self.root.after(0, self.log, message)

    def set_buttons_state(self, state):
        """Habilita o deshabilita los botones durante una consulta."""
        self.snmp_button.config(state=state)
        self.rmon_button.config(state=state)

    # --- CONSULTA SNMP REAL ---

    def query_snmp_real(self):
        """Inicia la consulta SNMP real en un hilo separado."""
        ip = self.ip_entry.get()
        community = self.community_entry.get()
        if not ip or not community:
            messagebox.showerror("Error", "Se requieren IP y Comunidad.")
            return

        self.log(f"Iniciando consulta SNMP a {ip} (Comunidad: {community})...")
        self.set_buttons_state(tk.DISABLED)
        
        # Ejecutar la consulta en un hilo para no bloquear la GUI
        query_thread = Thread(target=self._execute_snmp_query, 
                              args=(ip, community), 
                              daemon=True) # daemon=True hace que el hilo muera si cerramos la app
        query_thread.start()

    def _execute_snmp_query(self, ip, community):
        """
        Ejecuta la consulta SNMP para calcular eficiencia.
        Soporta ambas versiones de pysnmp (asyncio vs sync).
        """
        try:
            # OIDs para métricas de eficiencia (Interfaz 1 por defecto)
            oids = {
                'sysDescr': '1.3.6.1.2.1.1.1.0',
                'sysUpTime': '1.3.6.1.2.1.1.3.0',
                'sysName': '1.3.6.1.2.1.1.5.0',
                'ifSpeed': '1.3.6.1.2.1.2.2.1.5.1',       # Velocidad de interfaz (bps)
                'ifInOctets': '1.3.6.1.2.1.2.2.1.10.1',   # Bytes entrantes
                'ifOutOctets': '1.3.6.1.2.1.2.2.1.16.1',  # Bytes salientes
                'ifInErrors': '1.3.6.1.2.1.2.2.1.14.1',   # Errores entrantes
                'ifOutErrors': '1.3.6.1.2.1.2.2.1.20.1',  # Errores salientes
                'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11.1', # Paquetes unicast entrantes
                'ifOutUcastPkts': '1.3.6.1.2.1.2.2.1.17.1' # Paquetes unicast salientes
            }
            
            # Construir la lista de objetos OID
            var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]

            # --- DEFINICIÓN DE LA FUNCIÓN DE CONSULTA (ADAPTABLE) ---
            async def get_snmp_data_async():
                """Versión ASYNC (PySNMP v7+)"""
                snmp_engine = SnmpEngine()
                iterator = await get_cmd(
                    snmp_engine,
                    CommunityData(community, mpModel=0),
                    UdpTransportTarget((ip, 161), timeout=2, retries=2),
                    ContextData(),
                    *var_binds
                )
                
                # En v7+, iterator podría ser la respuesta directa o un iterable
                # Comúnmente retorna la tupla directamente en la llamada await
                return iterator

            def get_snmp_data_sync_legacy():
                """Versión SYNC (PySNMP v4)"""
                iterator = getCmd(
                    SnmpEngine(),
                    CommunityData(community, mpModel=0),
                    UdpTransportTarget((ip, 161), timeout=2, retries=2),
                    ContextData(),
                    *var_binds
                )
                return next(iterator)

            def fetch_data():
                """Wrapper para llamar a la función correcta"""
                if IS_V7:
                    # Ejecutar corrutina async desde hilo sincrónico
                    return asyncio.run(get_snmp_data_async())
                else:
                    return get_snmp_data_sync_legacy()

            # --- Muestreo 1 ---
            self.log_threadsafe(f"Tomando muestra inicial de {ip}...")
            t1 = time.time()
            
            errorIndication, errorStatus, errorIndex, varBinds = fetch_data()
            
            if errorIndication:
                 raise Exception(f"Indication: {errorIndication}")
            if errorStatus:
                 raise Exception(f"Status: {errorStatus.prettyPrint()}")

            # Mapear Data 1
            data1 = {}
            for vb in varBinds:
                 data1[str(vb[0])] = int(vb[1]) if vb[1].isSameTypeWith(ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1'))) else str(vb[1])

            self.log_threadsafe(f"Dispositivo: {data1.get(oids['sysName'], 'Unknown')}")

            # Esperar intervalo
            interval = 2
            self.log_threadsafe(f"Esperando {interval} segundos para calcular tasas...")
            time.sleep(interval)

            # --- Muestreo 2 ---
            self.log_threadsafe("Tomando segunda muestra...")
            t2 = time.time()
            
            errorIndication, errorStatus, errorIndex, varBinds = fetch_data()
            
            if errorIndication or errorStatus:
                 raise Exception("Error en segunda muestra")

            data2 = {}
            for vb in varBinds:
                 data2[str(vb[0])] = int(vb[1]) if vb[1].isSameTypeWith(ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1'))) else str(vb[1])

            # --- Cálculos ---
            delta_time = t2 - t1
            
            # Ancho de Banda
            bytes_1 = int(data1[oids['ifInOctets']]) + int(data1[oids['ifOutOctets']])
            bytes_2 = int(data2[oids['ifInOctets']]) + int(data2[oids['ifOutOctets']])
            delta_bytes = bytes_2 - bytes_1
            
            bps = (delta_bytes * 8) / delta_time
            if_speed_bps = int(data2[oids['ifSpeed']])
            if if_speed_bps == 0: if_speed_bps = 100000000 # Asumir 100Mbps si es 0 (virtual)
            
            utilization = (bps / if_speed_bps) * 100

            # Errores
            pkts_1 = int(data1[oids['ifInUcastPkts']]) + int(data1[oids['ifOutUcastPkts']])
            pkts_2 = int(data2[oids['ifInUcastPkts']]) + int(data2[oids['ifOutUcastPkts']])
            delta_pkts = pkts_2 - pkts_1
            
            errs_1 = int(data1[oids['ifInErrors']]) + int(data1[oids['ifOutErrors']])
            errs_2 = int(data2[oids['ifInErrors']]) + int(data2[oids['ifOutErrors']])
            delta_errs = errs_2 - errs_1
            
            error_rate = 0.0
            if delta_pkts > 0:
                error_rate = (delta_errs / delta_pkts) * 100

            # Reporte
            self.log_threadsafe("-" * 40)
            self.log_threadsafe("RESULTADOS DE EFICIENCIA DE RED (Real):")
            self.log_threadsafe(f"Duración: {delta_time:.2f} s")
            self.log_threadsafe(f"Velocidad Calc: {bps/1000:.2f} Kbps")
            self.log_threadsafe(f"Capacidad: {if_speed_bps/1000000:.1f} Mbps")
            self.log_threadsafe(f"Utilización: {utilization:.4f}%")
            self.log_threadsafe(f"Tasa de Errores: {error_rate:.4f}%")
            self.log_threadsafe("-" * 40)

        except Exception as e:
            self.log_threadsafe(f"FALLO: {e}")
            self.log_threadsafe("Verifica que el agente SNMP esté activo.")
        
        self.root.after(0, self.set_buttons_state, tk.NORMAL)
        self.root.after(0, self.log, "Consulta completada.")


    # --- TEST DE EFICIENCIA (PING REAL) ---

    def measure_network_efficiency(self):
        """Inicia el test de eficiencia de red (Ping) en un hilo separado."""
        ip = self.ip_entry.get()
        if not ip:
            messagebox.showerror("Error", "Por favor, ingrese una IP válida.")
            return

        self.log(f"Iniciando Test de Eficiencia (Ping) a {ip}...")
        self.set_buttons_state(tk.DISABLED)

        # Ejecutar en hilo para no congelar la GUI
        ping_thread = Thread(target=self._execute_ping_test, args=(ip,), daemon=True)
        ping_thread.start()

    def _execute_ping_test(self, ip):
        """Ejecuta el comando ping del sistema y analiza los resultados."""
        try:
            # Detectar SO para el argumento de conteo (-n para Windows, -c para Linux/Mac)
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '4', ip]

            # Ejecutar el comando ocultando la ventana de consola en Windows si es necesario
            startupinfo = None
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True # Decodificar salida como texto
            )
            
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.log_threadsafe(f"Respuesta de Ping recibida de {ip}:")
                self._parse_and_log_ping_output(stdout)
            else:
                self.log_threadsafe(f"El destino {ip} parece inalcanzable.")
                self.log_threadsafe(f"Detalle: {stderr or stdout}")

        except Exception as e:
            self.log_threadsafe(f"FALLO al ejecutar Ping: {e}")

        self.root.after(0, self.set_buttons_state, tk.NORMAL)
        self.root.after(0, self.log, "Test de eficiencia completado.")

    def _parse_and_log_ping_output(self, output):
        """Analiza la salida del ping para extraer métricas clave."""
        # Intentamos extraer métricas comunes con Regex
        
        # 1. Pérdida de paquetes
        # Windows: "Lost = 0 (0% loss)"
        # Linux: "0% packet loss"
        loss_match = re.search(r"(\d+)% (loss|packet loss)", output, re.IGNORECASE)
        if loss_match:
            self.log_threadsafe(f"  -> Pérdida de Paquetes: {loss_match.group(1)}%")
        
        # 2. Tiempos (RTT)
        # Windows: "Minimum = 10ms, Maximum = 20ms, Average = 15ms"
        # Linux: "rtt min/avg/max/mdev = 10.0/15.0/20.0/2.0 ms"
        
        # Windows Pattern
        win_time_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
        if win_time_match:
            self.log_threadsafe(f"  -> Latencia Mínima: {win_time_match.group(1)} ms")
            self.log_threadsafe(f"  -> Latencia Máxima: {win_time_match.group(2)} ms")
            self.log_threadsafe(f"  -> Latencia Promedio: {win_time_match.group(3)} ms (Eficiencia)")
            
        # Linux/Mac Pattern
        nix_time_match = re.search(r"min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/", output)
        if nix_time_match:
             self.log_threadsafe(f"  -> Latencia Mínima: {nix_time_match.group(1)} ms")
             self.log_threadsafe(f"  -> Latencia Promedio: {nix_time_match.group(2)} ms (Eficiencia)")
             self.log_threadsafe(f"  -> Latencia Máxima: {nix_time_match.group(3)} ms")

        # Si no matchea nada, imprimir las ultimas lineas crudas que suelen tener el resumen
        if not win_time_match and not nix_time_match:
            lines = output.strip().splitlines()
            # Tomar las últimas 2 lineas
            self.log_threadsafe("  -> " + lines[-2] if len(lines) > 1 else "")
            self.log_threadsafe("  -> " + lines[-1] if len(lines) > 0 else "")


# --- Punto de entrada principal ---
if __name__ == "__main__":
    if not PYSNMP_AVAILABLE:
        print("Error: No se puede iniciar la aplicación sin 'pysnmp'.")
        print("Por favor, instálelo con: pip install pysnmp")
    else:
        try:
            root = tk.Tk()
            app = NetworkMonitorApp(root)
            root.mainloop()
        except ImportError:
            print("Error: Se requiere el módulo 'tkinter'.")