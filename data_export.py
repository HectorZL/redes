"""
Módulo para exportar datos de monitoreo a CSV y JSON
"""
import json
import csv
from datetime import datetime
import os

class DataExporter:
    """Maneja la exportación de datos de monitoreo a diferentes formatos."""
    
    def __init__(self):
        self.export_dir = "exports"
        self._ensure_export_dir()
    
    def _ensure_export_dir(self):
        """Crea el directorio de exportación si no existe."""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def export_snmp_to_csv(self, snmp_data, num_agents):
        """
        Exporta datos SNMP a CSV.
        
        Args:
            snmp_data: Lista de diccionarios con datos de cada agente
            num_agents: Número de agentes
        
        Returns:
            str: Ruta del archivo creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/snmp_export_{timestamp}.csv"
        
        fieldnames = [
            'Agent', 'Device_Type', 'Device_Name', 'Uptime_Days',
            'Speed_Mbps', 'IN_Octets', 'OUT_Octets', 
            'IN_Packets', 'OUT_Packets', 'IN_Errors', 'OUT_Errors',
            'Total_Data_GB', 'Utilization_%', 'Error_Rate_%', 'Status'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for data in snmp_data:
                writer.writerow(data)
        
        return filename
    
    def export_snmp_to_json(self, snmp_data, num_agents):
        """
        Exporta datos SNMP a JSON.
        
        Args:
            snmp_data: Lista de diccionarios con datos de cada agente
            num_agents: Número de agentes
        
        Returns:
            str: Ruta del archivo creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/snmp_export_{timestamp}.json"
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "protocol": "SNMP",
            "num_agents": num_agents,
            "agents": snmp_data,
            "summary": self._calculate_snmp_summary(snmp_data)
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return filename
    
    def export_rmon_to_csv(self, rmon_data, num_agents):
        """
        Exporta datos RMON a CSV.
        
        Args:
            rmon_data: Diccionario con datos RMON
            num_agents: Número de agentes
        
        Returns:
            str: Ruta del archivo creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/rmon_export_{timestamp}.csv"
        
        # CSV para estadísticas por agente
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Agent', 'Drop_Events', 'Octets', 'Packets',
                'Broadcast_Pkts', 'Multicast_Pkts', 
                'CRC_Errors', 'Collisions', 'Fragments'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for agent_data in rmon_data.get('agents', []):
                writer.writerow(agent_data)
        
        # CSV adicional para alarmas
        alarms_file = filename.replace('.csv', '_alarms.csv')
        with open(alarms_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Alarm_Name', 'Threshold', 'Status', 'Current_Value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for alarm in rmon_data.get('alarms', []):
                writer.writerow(alarm)
        
        return filename
    
    def export_rmon_to_json(self, rmon_data, num_agents):
        """
        Exporta datos RMON a JSON.
        
        Args:
            rmon_data: Diccionario con datos RMON
            num_agents: Número de agentes
        
        Returns:
            str: Ruta del archivo creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/rmon_export_{timestamp}.json"
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "protocol": "RMON",
            "num_agents": num_agents,
            "data": rmon_data
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return filename
    
    def export_comparison_to_csv(self, comparison_data):
        """
        Exporta tabla comparativa SNMP vs RMON a CSV.
        
        Args:
            comparison_data: Diccionario con comparación
        
        Returns:
            str: Ruta del archivo creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/comparison_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Característica', 'SNMP', 'RMON']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in comparison_data:
                writer.writerow(row)
        
        return filename
    
    def _calculate_snmp_summary(self, snmp_data):
        """Calcula resumen de datos SNMP."""
        total_octets = sum(d.get('IN_Octets', 0) + d.get('OUT_Octets', 0) for d in snmp_data)
        total_packets = sum(d.get('IN_Packets', 0) + d.get('OUT_Packets', 0) for d in snmp_data)
        total_errors = sum(d.get('IN_Errors', 0) + d.get('OUT_Errors', 0) for d in snmp_data)
        avg_utilization = sum(d.get('Utilization_%', 0) for d in snmp_data) / len(snmp_data) if snmp_data else 0
        
        return {
            "total_data_gb": total_octets / 1e9,
            "total_packets": total_packets,
            "total_errors": total_errors,
            "average_utilization": round(avg_utilization, 2),
            "agents_optimal": sum(1 for d in snmp_data if d.get('Status') == 'ÓPTIMO'),
            "agents_alert": sum(1 for d in snmp_data if d.get('Status') == 'ALERTA')
        }
