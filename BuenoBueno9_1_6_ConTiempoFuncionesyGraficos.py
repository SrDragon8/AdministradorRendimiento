import psutil
import pynvml
import wmi
import time
import matplotlib.pyplot as plt
from tkinter import *

cpu_usage_history = []
memory_usage_history = []
gpu_usage_history = []

# Inicializar pynvml
pynvml.nvmlInit()

def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage

def get_cpu_temperature():
    w = wmi.WMI(namespace="root/OpenHardwareMonitor")
    temperature_infos = w.Sensor()
    for sensor in temperature_infos:
        if sensor.SensorType == 'Temperature' and sensor.Name == 'CPU Package':
            return sensor.Value
    return None

def get_cpu_model():
    w = wmi.WMI(namespace="root/CIMV2")
    processors = w.Win32_Processor()
    cpu_model = processors[0].Name
    return cpu_model

def get_gpu_usage():
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # 0 para la GPU 0
    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    return round(mem_info.used / mem_info.total * 100, 1)

def get_gpu_temperature():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
    return gpu_temp

def get_gpu_model():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(handle)
    return gpu_name

def get_memory_usage():
    memory = psutil.virtual_memory().total
    memory_free = psutil.virtual_memory().available
    memory_usage = ((memory - memory_free) / memory) * 100
    return round(memory_usage, 1)

def get_total_ram():
    w = wmi.WMI()
    ram_modules = w.Win32_PhysicalMemory()
    total_ram = sum(int(module.Capacity) for module in ram_modules)
    return total_ram

def get_ram_speed():
    w = wmi.WMI()
    ram_modules = w.Win32_PhysicalMemory()
    ram_speeds = [int(module.Speed) for module in ram_modules]
    if len(ram_speeds) > 0:
        return max(ram_speeds)
    return None

def get_storage_usage():
    partitions = psutil.disk_partitions()
    storage_usage = []
    for partition in partitions:
        partition_usage = psutil.disk_usage(partition.mountpoint)
        used_gb = partition_usage.used / (1024**3)  # Convertir a GB
        free_gb = partition_usage.free / (1024**3)  # Convertir a GB
        storage_usage.append((partition.device, used_gb, free_gb, partition_usage.percent))
    return storage_usage

def get_top_processes_by_resource_usage(num_processes):
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            pid = proc.pid
            name = proc.info['name']
            cpu_percent = round(proc.info['cpu_percent'], 1)
            memory_percent = round(proc.info['memory_percent'], 1)
            gpu_percent = get_gpu_usage()  # Obtener el uso de GPU del sistema
            processes.append((pid, name, cpu_percent, memory_percent, gpu_percent))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes[:num_processes]

def update_data(interval, num_processes):
    cpu_usage = get_cpu_usage()
    cpu_temperature = get_cpu_temperature()
    gpu_usage = get_gpu_usage()
    gpu_temperature = get_gpu_temperature()
    memory_usage = get_memory_usage()
    total_ram = get_total_ram()
    ram_speed = get_ram_speed()
    gpu_model = get_gpu_model()
    cpu_model = get_cpu_model()
    storage_usage = get_storage_usage()

    cpu_usage_history.append(cpu_usage)
    memory_usage_history.append(memory_usage)
    gpu_usage_history.append(gpu_usage)

    cpu_label.config(text=f"CPU Usage: {cpu_usage:.1f}%")
    cpu_temperature_label.config(text=f"CPU Temperature: {cpu_temperature}°C")
    gpu_usage_label.config(text=f"GPU Usage: {gpu_usage:.1f}%")
    gpu_temperature_label.config(text=f"GPU Temperature: {gpu_temperature}°C")
    memory_label.config(text=f"Memory Usage: {memory_usage:.1f}%")
    total_ram_label.config(text=f"Total RAM: {total_ram} bytes")
    ram_speed_label.config(text=f"RAM Speed: {ram_speed} MHz")
    gpu_model_label.config(text=f"GPU Model: {gpu_model}")
    cpu_model_label.config(text=f"CPU Model: {cpu_model}")

    process_info_label.config(text="Top Processes:")
    top_processes = get_top_processes_by_resource_usage(num_processes)
    for i, process in enumerate(top_processes):
        pid, name, cpu_percent, memory_percent, gpu_percent = process
        process_labels[i].config(text=f"{pid} - {name} - CPU: {cpu_percent:.1f}% - Memory: {memory_percent:.1f}% - GPU: {gpu_percent:.1f}%")

    storage_info_label.config(text="Storage Usage:")
    for i, storage in enumerate(storage_usage):
        device, used_gb, free_gb, percent = storage
        storage_labels[i].config(text=f"{device} - Used: {used_gb:.2f} GB - Free: {free_gb:.2f} GB - Usage: {percent}%")

    if len(cpu_usage_history) > 50:
        cpu_usage_history.pop(0)
    if len(memory_usage_history) > 50:
        memory_usage_history.pop(0)
    if len(gpu_usage_history) > 50:
        gpu_usage_history.pop(0)

    # Actualizar gráfico
    plt.clf()
    plt.plot(cpu_usage_history, label='CPU')
    plt.plot(memory_usage_history, label='Memory')
    plt.plot(gpu_usage_history, label='GPU')
    plt.xlabel('Time (s)')
    plt.ylabel('Usage (%)')
    plt.title('CPU, Memory, and GPU Usage Over Time')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.pause(interval)

    root.after(int(interval * 1000), update_data, interval, num_processes)

# Crear ventana principal
root = Tk()
root.title("System Monitor")
root.geometry("800x600")

# Etiquetas de CPU
cpu_label = Label(root, font=("Arial", 14))
cpu_label.pack()
cpu_temperature_label = Label(root, font=("Arial", 14))
cpu_temperature_label.pack()

# Etiquetas de GPU
gpu_usage_label = Label(root, font=("Arial", 14))
gpu_usage_label.pack()
gpu_temperature_label = Label(root, font=("Arial", 14))
gpu_temperature_label.pack()

# Etiqueta de uso de memoria
memory_label = Label(root, font=("Arial", 14))
memory_label.pack()

# Etiqueta de RAM total
total_ram_label = Label(root, font=("Arial", 14))
total_ram_label.pack()

# Etiqueta de velocidad de RAM
ram_speed_label = Label(root, font=("Arial", 14))
ram_speed_label.pack()

# Etiqueta de modelo de GPU
gpu_model_label = Label(root, font=("Arial", 14))
gpu_model_label.pack()

# Etiqueta de modelo de CPU
cpu_model_label = Label(root, font=("Arial", 14))
cpu_model_label.pack()

# Etiqueta de información de procesos
process_info_label = Label(root, font=("Arial", 14))
process_info_label.pack()

# Etiquetas de procesos
process_labels = []
for _ in range(5):
    process_label = Label(root, font=("Arial", 12))
    process_label.pack()
    process_labels.append(process_label)

# Etiqueta de información de almacenamiento
storage_info_label = Label(root, font=("Arial", 14))
storage_info_label.pack()

# Etiquetas de almacenamiento
storage_labels = []
for _ in range(3):
    storage_label = Label(root, font=("Arial", 12))
    storage_label.pack()
    storage_labels.append(storage_label)

# Configuración de gráfico
plt.rcParams["figure.figsize"] = (8, 4)
plt.ion()

# Ejecutar función de actualización de datos
update_data(1, 5)

root.mainloop()

# Finalizar pynvml
pynvml.nvmlShutdown()
