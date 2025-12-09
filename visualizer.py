"""
Módulo para visualización de datos con gráficos
"""
import matplotlib
matplotlib.use('TkAgg')  # Backend para Tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

class DataVisualizer:
    """Maneja la visualización de datos con gráficos."""
    
    def __init__(self):
        self.fig = None
        self.canvas = None
    
    def plot_utilization_history(self, history_data, parent_window):
        """
        Crea gráfico de historial de utilización temporal.
        
        Args:
            history_data: Lista de dict con historial RMON
            parent_window: Ventana padre para el gráfico
        """
        top = tk.Toplevel(parent_window)
        top.title("Gráfico de Utilización Temporal")
        top.geometry("800x600")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extraer datos
        timestamps = []
        utilizations = []
        
        for entry in history_data:
            timestamps.append(entry['timestamp'])
            utilizations.append(entry['utilization'])
        
        # Crear gráfico de línea
        ax.plot(timestamps, utilizations, marker='o', linestyle='-', linewidth=2, markersize=8)
        ax.set_xlabel('Tiempo', fontsize=12)
        ax.set_ylabel('Utilización (%)', fontsize=12)
        ax.set_title('Historial de Utilización de Red', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        
        # Agregar línea de umbral
        ax.axhline(y=80, color='r', linestyle='--', label='Umbral (80%)')
        ax.legend()
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Incrustar en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Botón cerrar
        btn_close = ttk.Button(top, text="Cerrar", command=top.destroy)
        btn_close.pack(pady=10)
    
    def plot_packet_distribution(self, rmon_data, parent_window):
        """
        Crea gráfico de distribución de paquetes.
        
        Args:
            rmon_data: Diccionario con datos RMON
            parent_window: Ventana padre
        """
        top = tk.Toplevel(parent_window)
        top.title("Distribución de Paquetes")
        top.geometry("800x600")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gráfico 1: Paquetes por agente
        agents = [f"Agent {i+1}" for i in range(len(rmon_data.get('agents', [])))]
        packets = [agent['Packets'] for agent in rmon_data.get('agents', [])]
        
        ax1.bar(agents, packets, color='skyblue', edgecolor='navy')
        ax1.set_xlabel('Agentes', fontsize=12)
        ax1.set_ylabel('Paquetes', fontsize=12)
        ax1.set_title('Paquetes por Agente', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Rotar etiquetas si hay muchos agentes
        if len(agents) > 3:
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Gráfico 2: Tipos de tráfico (Pie chart)
        if rmon_data.get('agents'):
            first_agent = rmon_data['agents'][0]
            labels = ['Unicast', 'Broadcast', 'Multicast']
            sizes = [
                first_agent['Packets'] - first_agent['Broadcast_Pkts'] - first_agent['Multicast_Pkts'],
                first_agent['Broadcast_Pkts'],
                first_agent['Multicast_Pkts']
            ]
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            explode = (0.05, 0, 0)
            
            ax2.pie(sizes, explode=explode, labels=labels, colors=colors,
                    autopct='%1.1f%%', shadow=True, startangle=90)
            ax2.set_title(f'Distribución de Tráfico\n(Agent 1)', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Incrustar en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Botón cerrar
        btn_close = ttk.Button(top, text="Cerrar", command=top.destroy)
        btn_close.pack(pady=10)
    
    def show_comparison_table(self, parent_window):
        """
        Muestra una tabla comparativa entre SNMP y RMON.
        
        Args:
            parent_window: Ventana padre
        """
        top = tk.Toplevel(parent_window)
        top.title("Comparativa SNMP vs RMON")
        top.geometry("900x500")
        
        # Frame principal
        frame = ttk.Frame(top, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(frame, text="Comparativa: SNMP vs RMON", 
                                font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=10)
        
        # Crear Treeview
        columns = ('Característica', 'SNMP', 'RMON')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=300, anchor='w')
        
        # Datos comparativos
        comparison_data = [
            ('Objetivo Principal', 'Gestión de dispositivos individuales', 'Monitoreo de segmentos de red'),
            ('Alcance', 'Nivel de dispositivo', 'Nivel de red/segmento'),
            ('Agente Requerido', 'Sí (en cada dispositivo)', 'Sí (puede ser dedicado)'),
            ('Grupos MIB', '11 grupos (RFC 1213)', '9 grupos + RMON2 (RFC 2819)'),
            ('Estadísticas', 'Básicas por interfaz', 'Avanzadas con historial'),
            ('Historial', 'No nativo', 'Sí, con timestamps'),
            ('Alarmas', 'Traps básicos', 'Sistema completo de alarmas'),
            ('Análisis de Hosts', 'No', 'Sí (Top N hosts)'),
            ('Tráfico por Protocolo', 'Limitado', 'Detallado'),
            ('Consumo de Recursos', 'Bajo', 'Medio-Alto'),
            ('Complejidad', 'Baja', 'Media-Alta'),
            ('Mejor Para', 'Monitoreo básico, gestión', 'Análisis profundo, troubleshooting'),
            ('RFC Principal', 'RFC 1157, 3416', 'RFC 2819, 4502'),
            ('Overhead de Red', 'Bajo', 'Medio'),
            ('Tiempo Real', 'Sí', 'Sí'),
        ]
        
        # Insertar datos
        for item in comparison_data:
            tree.insert('', tk.END, values=item)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Frame para botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        # Botón exportar
        def export_comparison():
            from data_export import DataExporter
            exporter = DataExporter()
            comparison_list = [
                {'Característica': item[0], 'SNMP': item[1], 'RMON': item[2]}
                for item in comparison_data
            ]
            filename = exporter.export_comparison_to_csv(comparison_list)
            tk.messagebox.showinfo("Exportación Exitosa", 
                                   f"Tabla comparativa exportada a:\n{filename}")
        
        btn_export = ttk.Button(btn_frame, text="Exportar a CSV", command=export_comparison)
        btn_export.pack(side=tk.LEFT, padx=5)
        
        btn_close = ttk.Button(btn_frame, text="Cerrar", command=top.destroy)
        btn_close.pack(side=tk.LEFT, padx=5)
