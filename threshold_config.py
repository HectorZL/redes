"""
Diálogo para configurar umbrales de alarma personalizados
"""
import tkinter as tk
from tkinter import ttk, messagebox

class ThresholdConfigDialog:
    """Ventana de configuración de umbrales de alarma."""
    
    def __init__(self, parent, current_thresholds, callback):
        """
        Args:
            parent: Ventana padre
            current_thresholds: Dict con umbrales actuales
            callback: Función a llamar al guardar cambios
        """
        self.top = tk.Toplevel(parent)
        self.top.title("Configuración de Umbrales de Alarma")
        self.top.geometry("500x400")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.current_thresholds = current_thresholds.copy()
        self.callback = callback
        self.entries = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Crea la interfaz de configuración."""
        # Frame principal
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, 
                                text="⚙️ Configuración de Umbrales",
                                font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame para configuraciones
        config_frame = ttk.LabelFrame(main_frame, text="Umbrales de Alarma", padding="15")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configuraciones individuales
        configs = [
            ('utilization', 'Utilización Máxima (%)', 0, 100, 
             'Porcentaje máximo de utilización antes de generar alarma'),
            ('error_rate', 'Tasa de Error Máxima (%)', 0, 10, 
             'Porcentaje máximo de errores aceptable'),
            ('broadcast', 'Paquetes Broadcast Máx. (/s)', 0, 50000, 
             'Número máximo de paquetes broadcast por segundo'),
            ('collisions', 'Colisiones Máximas (/min)', 0, 1000, 
             'Número máximo de colisiones por minuto')
        ]
        
        for i, (key, label, min_val, max_val, desc) in enumerate(configs):
            # Label
            lbl = ttk.Label(config_frame, text=label, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i*3, column=0, sticky='w', pady=(10, 2))
            
            # Frame para entrada y valor actual
            entry_frame = ttk.Frame(config_frame)
            entry_frame.grid(row=i*3+1, column=0, sticky='ew', pady=2)
            
            # Entrada
            entry = ttk.Entry(entry_frame, width=15)
            entry.pack(side=tk.LEFT, padx=(0, 10))
            entry.insert(0, str(self.current_thresholds.get(key, 0)))
            self.entries[key] = entry
            
            # Indicador de valor actual
            current_lbl = ttk.Label(entry_frame, 
                                    text=f"Actual: {self.current_thresholds.get(key, 0)}",
                                    foreground='gray')
            current_lbl.pack(side=tk.LEFT)
            
            # Descripción
            desc_lbl = ttk.Label(config_frame, text=desc, 
                                font=("Segoe UI", 8), foreground='gray')
            desc_lbl.grid(row=i*3+2, column=0, sticky='w', pady=(0, 5))
        
        config_frame.columnconfigure(0, weight=1)
        
        # Frame informativo
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = ("💡 Estos umbrales se aplicarán a futuras mediciones.\n"
                    "Los valores más bajos generarán más alarmas.")
        info_label = ttk.Label(info_frame, text=info_text, 
                              font=("Segoe UI", 9), 
                              foreground='#0066cc',
                              justify='left')
        info_label.pack()
        
        # Frame de botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Botón Restaurar Valores Por Defecto
        btn_reset = ttk.Button(btn_frame, text="Restaurar Predeterminados", 
                              command=self._reset_defaults)
        btn_reset.pack(side=tk.LEFT, padx=5)
        
        # Botón Cancelar
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", 
                               command=self.top.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        # Botón Guardar
        btn_save = ttk.Button(btn_frame, text="Guardar", 
                             command=self._save_changes)
        btn_save.pack(side=tk.RIGHT, padx=5)
    
    def _reset_defaults(self):
        """Restaura valores predeterminados."""
        defaults = {
            'utilization': 80.0,
            'error_rate': 1.0,
            'broadcast': 10000,
            'collisions': 100
        }
        
        for key, value in defaults.items():
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(value))
        
        messagebox.showinfo("Restaurado", 
                          "Valores predeterminados restaurados.\nClick 'Guardar' para aplicar.")
    
    def _save_changes(self):
        """Valida y guarda los cambios."""
        try:
            new_thresholds = {}
            
            for key, entry in self.entries.items():
                value = float(entry.get())
                
                # Validaciones básicas
                if value < 0:
                    raise ValueError(f"El valor para {key} no puede ser negativo")
                
                if key == 'utilization' and (value < 0 or value > 100):
                    raise ValueError("La utilización debe estar entre 0 y 100%")
                
                if key == 'error_rate' and value > 100:
                    raise ValueError("La tasa de error debe estar entre 0 y 100%")
                
                new_thresholds[key] = value
            
            # Llamar al callback con los nuevos valores
            if self.callback:
                self.callback(new_thresholds)
            
            messagebox.showinfo("Guardado", 
                              "Umbrales actualizados exitosamente.\n"
                              "Se aplicarán en las próximas mediciones.")
            self.top.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
