import time
import subprocess
import platform
import re
import asyncio
from threading import Thread

# --- GESTIÓN DE IMPORTACIONES PYSNMP ---
PYSNMP_AVAILABLE = False
IS_V7 = False
try:
    # Intento v7+ (Asyncio nativo)
    from pysnmp.hlapi.asyncio import (get_cmd, SnmpEngine, CommunityData, 
                                      UdpTransportTarget, ContextData, 
                                      ObjectType, ObjectIdentity)
    PYSNMP_AVAILABLE = True
    IS_V7 = True
except ImportError:
    try:
        # Fallback v4/v6 (Sync/Legacy)
        from pysnmp.hlapi import (getCmd, SnmpEngine, CommunityData, 
                                       UdpTransportTarget, ContextData, 
                                       ObjectType, ObjectIdentity)
        PYSNMP_AVAILABLE = True
        IS_V7 = False
    except ImportError as e:
        print(f"[Logic] Error importando pysnmp: {e}")

class NetworkLogic:
    """
    Encapsula toda la lógica de monitorización (SNMP y Ping).
    No depende de Tkinter directamente. Usa un callback para logging.
    """
    def __init__(self, log_callback):
        self.log_callback = log_callback # Función para reportar logs (debe ser thread-safe o manejarlo en GUI)

    def is_snmp_available(self):
        return PYSNMP_AVAILABLE

    def run_snmp_test(self, ip, community):
        """Lanza el test SNMP en un hilo aparte."""
        t = Thread(target=self._execute_snmp_query, args=(ip, community), daemon=True)
        t.start()

    def run_ping_test(self, ip):
        """Lanza el test Ping en un hilo aparte."""
        t = Thread(target=self._execute_ping_test, args=(ip,), daemon=True)
        t.start()

    # --- IMPLEMENTACIÓN SNMP ---
    def _execute_snmp_query(self, ip, community):
        try:
            self.log_callback(f"Iniciando consulta SNMP a {ip}...")
            
            # OIDs
            oids = {
                'sysDescr': '1.3.6.1.2.1.1.1.0',
                'sysUpTime': '1.3.6.1.2.1.1.3.0',
                'sysName': '1.3.6.1.2.1.1.5.0',
                'ifSpeed': '1.3.6.1.2.1.2.2.1.5.1',
                'ifInOctets': '1.3.6.1.2.1.2.2.1.10.1',
                'ifOutOctets': '1.3.6.1.2.1.2.2.1.16.1',
                'ifInErrors': '1.3.6.1.2.1.2.2.1.14.1',
                'ifOutErrors': '1.3.6.1.2.1.2.2.1.20.1',
                'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11.1',
                'ifOutUcastPkts': '1.3.6.1.2.1.2.2.1.17.1'
            }
            var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]

            # Helpers de obtención de datos
            async def get_async():
                snmp_engine = SnmpEngine()
                return await get_cmd(snmp_engine, CommunityData(community, mpModel=0),
                                     UdpTransportTarget((ip, 161), timeout=2, retries=2),
                                     ContextData(), *var_binds)

            def get_sync():
                return next(getCmd(SnmpEngine(), CommunityData(community, mpModel=0),
                                   UdpTransportTarget((ip, 161), timeout=2, retries=2),
                                   ContextData(), *var_binds))

            def fetch():
                if IS_V7: return asyncio.run(get_async())
                else: return get_sync()

            # Muestra 1
            self.log_threadsafe("Tomando Muestra 1...")
            t1 = time.time()
            errInd, errStat, errIdx, vb1 = fetch()
            if errInd or errStat: raise Exception(f"{errInd or errStat}")
            
            data1 = {str(v[0]): (int(v[1]) if v[1].isSameTypeWith(ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1'))) else str(v[1])) for v in vb1}
            self.log_threadsafe(f"Dispositivo: {data1.get(oids['sysName'], 'N/A')}")

            # Espera
            time.sleep(2)

            # Muestra 2
            self.log_threadsafe("Tomando Muestra 2...")
            t2 = time.time()
            errInd, errStat, errIdx, vb2 = fetch()
            if errInd or errStat: raise Exception("Error en muestra 2")
            
            data2 = {str(v[0]): (int(v[1]) if v[1].isSameTypeWith(ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1'))) else str(v[1])) for v in vb2}

            # Cálculos
            delta_t = t2 - t1
            bytes_1 = int(data1[oids['ifInOctets']]) + int(data1[oids['ifOutOctets']])
            bytes_2 = int(data2[oids['ifInOctets']]) + int(data2[oids['ifOutOctets']])
            bps = ((bytes_2 - bytes_1) * 8) / delta_t
            
            speed = int(data2[oids['ifSpeed']])
            if speed == 0: speed = 100_000_000
            
            util = (bps / speed) * 100
            
            # Errores
            pkts_1 = int(data1[oids['ifInUcastPkts']]) + int(data1[oids['ifOutUcastPkts']])
            pkts_2 = int(data2[oids['ifInUcastPkts']]) + int(data2[oids['ifOutUcastPkts']])
            delta_pkts = pkts_2 - pkts_1
            errs = (int(data2[oids['ifInErrors']]) + int(data2[oids['ifOutErrors']])) - \
                   (int(data1[oids['ifInErrors']]) + int(data1[oids['ifOutErrors']]))
            
            err_rate = (errs / delta_pkts * 100) if delta_pkts > 0 else 0.0

            self.log_threadsafe("-" * 30)
            self.log_threadsafe(f"RESULTADOS ({delta_t:.1f}s):")
            self.log_threadsafe(f"Velocidad: {bps/1000:.2f} Kbps")
            self.log_threadsafe(f"Utilización: {util:.2f}%")
            self.log_threadsafe(f"Error Rate: {err_rate:.4f}% ({errs} err)")
            self.log_threadsafe("-" * 30)

        except Exception as e:
            self.log_threadsafe(f"Error SNMP: {e}")
        
        self.log_threadsafe("FIN SNMP.")

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
                # Parseo básico
                loss = re.search(r"(\d+)% (loss|packet loss|perdidos)", out)
                if loss: self.log_threadsafe(f"Pérdida: {loss.group(1)}%")
                
                # Tiempos (Simplificado para buscar 'Media' o 'Average')
                avg = re.search(r"(Media|Average) = (\d+)ms", out)
                if avg: self.log_threadsafe(f"Latencia Media: {avg.group(2)}ms")
                else: self.log_threadsafe("Ver output crudo para latencia.")
            else:
                self.log_threadsafe(f"Ping falló: {err or out}")

        except Exception as e:
            self.log_threadsafe(f"Error Ping: {e}")
        
        self.log_threadsafe("FIN Ping.")

    def log_threadsafe(self, msg):
        """Helper para enviar al callback."""
        if self.log_callback:
            self.log_callback(msg)
