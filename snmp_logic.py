import time
import subprocess
import platform
import re
import random
from threading import Thread

class NetworkLogic:
    """
    Encapsula toda la lógica de monitorización (SNMP Mock, RMON Mock y Ping).
    No depende de Tkinter directamente. Usa un callback para logging.
    """
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def is_snmp_available(self):
        return True  # Siempre disponible en modo simulado

    def run_snmp_test(self, ip, community, num_agents=1):
        """Lanza el test SNMP simulado en un hilo aparte."""
        t = Thread(target=self._execute_snmp_mock, args=(ip, community, num_agents), daemon=True)
        t.start()

    def run_ping_test(self, ip):
        """Lanza el test Ping en un hilo aparte."""
        t = Thread(target=self._execute_ping_test, args=(ip,), daemon=True)
        t.start()

    def run_rmon_test(self, ip, num_agents=1):
        """Lanza el test RMON simulado en un hilo aparte."""
        t = Thread(target=self._execute_rmon_mock, args=(ip, num_agents), daemon=True)
        t.start()

    # --- IMPLEMENTACIÓN SNMP SIMULADO ---
    def _execute_snmp_mock(self, ip_str, community, num_agents=1):
        """Simula consulta SNMP con datos mock para demostración académica."""
        try:
            self.log_threadsafe(f"Iniciando Monitoreo SNMP a {ip_str}...")
            self.log_threadsafe(f"NOTA: Datos simulados para {num_agents} agente(s)")
            self.log_threadsafe("=" * 50)
            time.sleep(0.5)

            # Generar datos para cada agente
            for agent_num in range(1, num_agents + 1):
                self.log_threadsafe(f"\n🖥️  AGENTE #{agent_num} - Dispositivo-{agent_num:02d}")
                self.log_threadsafe("-" * 40)
                
                # Información del sistema
                device_types = ["Router Cisco", "Switch HP", "Firewall Palo Alto", 
                               "Access Point Ubiquiti", "Server Linux"]
                uptime_days = random.randint(1, 365)
                
                self.log_threadsafe(f"  Tipo: {random.choice(device_types)}")
                self.log_threadsafe(f"  Nombre: DEVICE-{agent_num:02d}.local")
                self.log_threadsafe(f"  Uptime: {uptime_days} días")
                
                # Estadísticas de interfaz
                time.sleep(0.3)
                self.log_threadsafe("\n  📊 Estadísticas de Interfaz:")
                
                speed_mbps = random.choice([100, 1000, 10000])
                in_octets = random.randint(1000000000, 5000000000)
                out_octets = random.randint(800000000, 4000000000)
                in_packets = random.randint(500000, 2000000)
                out_packets = random.randint(400000, 1800000)
                in_errors = random.randint(0, 100)
                out_errors = random.randint(0, 80)
                
                self.log_threadsafe(f"    Velocidad: {speed_mbps} Mbps")
                self.log_threadsafe(f"    IN - Octetos: {in_octets:,} ({in_octets/1e9:.2f} GB)")
                self.log_threadsafe(f"    OUT - Octetos: {out_octets:,} ({out_octets/1e9:.2f} GB)")
                self.log_threadsafe(f"    IN - Paquetes: {in_packets:,}")
                self.log_threadsafe(f"    OUT - Paquetes: {out_packets:,}")
                self.log_threadsafe(f"    Errores IN/OUT: {in_errors}/{out_errors}")
                
                # Cálculos de eficiencia
                total_data_gb = (in_octets + out_octets) / 1e9
                util_percent = random.uniform(25.0, 85.0)
                err_rate = ((in_errors + out_errors) / (in_packets + out_packets)) * 100 if (in_packets + out_packets) > 0 else 0
                
                self.log_threadsafe(f"\n  📈 Análisis de Rendimiento:")
                self.log_threadsafe(f"    Tráfico Total: {total_data_gb:.2f} GB")
                self.log_threadsafe(f"    Utilización: {util_percent:.1f}%")
                self.log_threadsafe(f"    Tasa de Error: {err_rate:.4f}%")
                
                # Estado de la red
                status_icon = "✅" if util_percent < 80 and err_rate < 0.1 else "⚠️"
                status = "ÓPTIMO" if util_percent < 80 and err_rate < 0.1 else "ALERTA"
                self.log_threadsafe(f"    Estado: {status_icon} {status}")
                
                time.sleep(0.3)
            
            # Resumen global
            self.log_threadsafe("\n" + "=" * 50)
            self.log_threadsafe("📋 RESUMEN GLOBAL SNMP:")
            self.log_threadsafe(f"  ✓ Agentes monitoreados: {num_agents}")
            self.log_threadsafe(f"  ✓ Comunidad: {community}")
            self.log_threadsafe(f"  ✓ Protocolo: SNMPv2c")
            self.log_threadsafe("=" * 50)
            
        except Exception as e:
            self.log_threadsafe(f"Error en simulación SNMP: {e}")
        
        self.log_threadsafe("FIN Monitoreo SNMP.\n")

    # --- IMPLEMENTACIÓN PING ---
    def _execute_ping_test(self, ip):
        try:
            self.log_threadsafe(f"Haciendo PING a {ip}...")
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            cmd = ['ping', param, '4', ip]
            
            si = None
            if platform.system().lower() == 'windows':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=si)
            out, err = proc.communicate()
            
            if proc.returncode == 0:
                self.log_threadsafe("Ping exitoso.")
                loss = re.search(r"(\d+)% (loss|packet loss|perdidos)", out)
                if loss: self.log_threadsafe(f"Pérdida: {loss.group(1)}%")
                
                avg = re.search(r"(Media|Average) = (\d+)ms", out)
                if avg: self.log_threadsafe(f"Latencia Media: {avg.group(2)}ms")
                else: self.log_threadsafe("Ver output crudo para latencia.")
            else:
                self.log_threadsafe(f"Ping falló: {err or out}")

        except Exception as e:
            self.log_threadsafe(f"Error Ping: {e}")
        
        self.log_threadsafe("FIN Ping.\n")

    # --- IMPLEMENTACIÓN RMON SIMULADO ---
    def _execute_rmon_mock(self, ip_str, num_agents=1):
        """Simula consulta RMON con datos mock para demostración académica."""
        try:
            self.log_threadsafe(f"Iniciando Monitoreo RMON a {ip_str}...")
            self.log_threadsafe(f"NOTA: Datos simulados para {num_agents} agente(s)")
            self.log_threadsafe("=" * 50)
            time.sleep(0.5)

            # Datos agregados para todos los agentes
            total_drop_events = 0
            total_octets = 0
            total_pkts = 0
            total_errors = 0
            
            # === RMON Grupo 1: Estadísticas Ethernet (por agente) ===
            self.log_threadsafe("\n📊 RMON Grupo 1: Estadísticas Ethernet")
            
            for agent_num in range(1, num_agents + 1):
                self.log_threadsafe(f"\n  🖥️  Agente #{agent_num}:")
                
                drop_events = random.randint(5, 50)
                octets = random.randint(500000000, 2000000000)
                pkts = random.randint(1000000, 5000000)
                broadcast_pkts = random.randint(10000, 50000)
                multicast_pkts = random.randint(5000, 25000)
                crc_errors = random.randint(0, 100)
                collisions = random.randint(0, 50)
                
                total_drop_events += drop_events
                total_octets += octets
                total_pkts += pkts
                total_errors += (crc_errors + collisions)
                
                self.log_threadsafe(f"    Eventos de descarte: {drop_events}")
                self.log_threadsafe(f"    Octetos: {octets:,} bytes ({octets/1e9:.2f} GB)")
                self.log_threadsafe(f"    Paquetes: {pkts:,}")
                self.log_threadsafe(f"    Broadcast: {broadcast_pkts:,} | Multicast: {multicast_pkts:,}")
                self.log_threadsafe(f"    Errores CRC: {crc_errors} | Colisiones: {collisions}")
                
                time.sleep(0.3)
            
            # === RMON Grupo 2: Historial ===
            time.sleep(0.5)
            self.log_threadsafe("\n📈 RMON Grupo 2: Historial de Tráfico")
            self.log_threadsafe("  Últimas 5 muestras (intervalos de 30s):\n")
            
            for i in range(5, 0, -1):
                sample_octets = random.randint(1000000, 5000000) * num_agents
                sample_pkts = random.randint(5000, 25000) * num_agents
                sample_util = random.uniform(15.0, 85.0)
                timestamp = f"T-{i*30}s"
                
                self.log_threadsafe(f"  [{timestamp}] "
                                   f"Octets: {sample_octets:,}, "
                                   f"Pkts: {sample_pkts:,}, "
                                   f"Util: {sample_util:.1f}%")
            
            # === RMON Grupo 3: Alarmas ===
            time.sleep(0.5)
            self.log_threadsafe("\n⚠️  RMON Grupo 3: Alarmas Configuradas\n")
            
            alarm_scenarios = [
                ("Utilización Alta", "> 80%", random.choice(["Normal", "ALERTA"]), random.uniform(45, 90)),
                ("Tasa de Errores", "> 1%", random.choice(["Normal", "Normal", "WARNING"]), random.uniform(0.1, 1.5)),
                ("Paquetes Broadcast", "> 10000/s", "Normal", random.randint(1000, 9000)),
                ("Colisiones", "> 100/min", random.choice(["Normal", "Normal", "Normal", "WARNING"]), random.randint(10, 150))
            ]
            
            for alarm_name, threshold, status, current_val in alarm_scenarios:
                status_icon = "✓" if status == "Normal" else "⚠"
                self.log_threadsafe(f"  {status_icon} {alarm_name}: {status} "
                                   f"(Umbral: {threshold}, Actual: {current_val:.1f})")
            
            # === RMON Grupo 4: Hosts detectados ===
            time.sleep(0.5)
            self.log_threadsafe("\n💻 RMON Grupo 4: Top Hosts por Tráfico\n")
            
            # Mostrar hasta 5 hosts o num_agents*2, lo que sea menor
            num_hosts = min(5, num_agents * 2)
            for i in range(1, num_hosts + 1):
                mac = f"00:1A:2B:{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"
                pkts_in = random.randint(10000, 100000)
                pkts_out = random.randint(10000, 100000)
                octets_total = random.randint(50000000, 500000000)
                
                self.log_threadsafe(f"  Host {i} (MAC: {mac})")
                self.log_threadsafe(f"    Pkts IN: {pkts_in:,}, OUT: {pkts_out:,}")
                self.log_threadsafe(f"    Tráfico: {octets_total/1e6:.2f} MB")
            
            # === Resumen Final ===
            time.sleep(0.3)
            self.log_threadsafe("\n" + "=" * 50)
            self.log_threadsafe("📋 RESUMEN GLOBAL RMON:")
            efficiency = 100 - ((total_drop_events + total_errors) / total_pkts * 100)
            self.log_threadsafe(f"  ✓ Agentes monitoreados: {num_agents}")
            self.log_threadsafe(f"  ✓ Eficiencia de red: {efficiency:.2f}%")
            self.log_threadsafe(f"  ✓ Paquetes procesados: {total_pkts:,}")
            self.log_threadsafe(f"  ✓ Volumen total: {total_octets/1e9:.2f} GB")
            
            active_alarms = sum(1 for _, _, status, _ in alarm_scenarios if status != "Normal")
            self.log_threadsafe(f"  ⚠  Alarmas activas: {active_alarms}/4")
            self.log_threadsafe("=" * 50)
            
        except Exception as e:
            self.log_threadsafe(f"Error en simulación RMON: {e}")
        
        self.log_threadsafe("FIN Monitoreo RMON.\n")

    def log_threadsafe(self, msg):
        """Helper para enviar al callback."""
        if self.log_callback:
            self.log_callback(msg)
