import psutil
import pynvml
import wmi
import time
import matplotlib.pyplot as plt
from tkinter import *

cpu_usage_history = []
memory_usage_history = []

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

def get_gpu_usage(pid):
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
        storage_usage.append((partition.device, partition_usage.used, partition_usage.free, partition_usage.percent))
    return storage_usage

def get_network_usage():
    network = psutil.net_io_counters()
    network_usage = network.bytes_sent + network.bytes_recv
    return network_usage

def get_top_processes_by_resource_usage(num_processes):
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            pid = proc.pid
            name = proc.info['name']
            cpu_percent = round(proc.info['cpu_percent'], 1)
            memory_percent = round(proc.info['memory_percent'], 1)
            gpu_percent = get_gpu_usage(pid)  # Obtener el uso de GPU del proceso
            processes.append((pid, name, cpu_percent, memory_percent, gpu_percent))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes[:num_processes]

def update_data(interval, num_processes):
    cpu_usage = get_cpu_usage()
    cpu_temperature = get_cpu_temperature()
    gpu_temperature = get_gpu_temperature()
    memory_usage = get_memory_usage()
    total_ram = get_total_ram()
    ram_speed = get_ram_speed()
    gpu_model = get_gpu_model()
    cpu_model = get_cpu_model()
    storage_usage = get_storage_usage()

    cpu_usage_history.append(cpu_usage)
    memory_usage_history.append(memory_usage)

    cpu_label.config(text=f"CPU Usage: {cpu_usage:.1f}%")
    cpu_temperature_label.config(text=f"CPU Temperature: {cpu_temperature}°C")
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
    storage_usage = get_storage_usage()
    for i, storage in enumerate(storage_usage):
        device, used, free, percent = storage
        storage_labels[i].config(text=f"{device} - Used: {used} bytes - Free: {free} bytes - Usage: {percent:.1f}%")

    if len(cpu_usage_history) > 50:
        cpu_usage_history.pop(0)
    if len(memory_usage_history) > 50:
        memory_usage_history.pop(0)

    # Actualizar gráfico
    plt.clf()
    plt.subplot(2, 1, 1)
    plt.plot(cpu_usage_history, 'b-', label='CPU Usage')
    plt.ylabel('Usage (%)')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(memory_usage_history, 'g-', label='Memory Usage')
    plt.xlabel('Time (s)')
    plt.ylabel('Usage (%)')
    plt.legend()

    plt.tight_layout()
    plt.pause(0.001)

    window.after(interval * 1000, lambda: update_data(interval, num_processes))

# Crear la ventana principal
window = Tk()
window.title("System Monitor")

# Crear etiquetas para mostrar los datos
cpu_label = Label(window, text="CPU Usage: ")
cpu_label.pack()

cpu_temperature_label = Label(window, text="CPU Temperature: ")
cpu_temperature_label.pack()

gpu_temperature_label = Label(window, text="GPU Temperature: ")
gpu_temperature_label.pack()

memory_label = Label(window, text="Memory Usage: ")
memory_label.pack()

total_ram_label = Label(window, text="Total RAM: ")
total_ram_label.pack()

ram_speed_label = Label(window, text="RAM Speed: ")
ram_speed_label.pack()

gpu_model_label = Label(window, text="GPU Model: ")
gpu_model_label.pack()

cpu_model_label = Label(window, text="CPU Model: ")
cpu_model_label.pack()

process_info_label = Label(window, text="Top Processes:")
process_info_label.pack()

process_labels = []
for i in range(5):
    label = Label(window, text="")
    label.pack()
    process_labels.append(label)

storage_info_label = Label(window, text="Storage Usage:")
storage_info_label.pack()

storage_labels = []
for i in range(len(psutil.disk_partitions())):
    label = Label(window, text="")
    label.pack()
    storage_labels.append(label)

# Botón para comenzar el monitoreo
start_button = Button(window, text="Comenzar monitoreo", command=lambda: update_data(5, 5))
start_button.pack()

# Ejecutar la ventana principal
window.mainloop()

# Cerrar pynvml al finalizar
pynvml.nvmlShutdown()

'''
En este código se realizaron las siguientes modificaciones:

1. Se agregó un paréntesis en la línea 121 al llamar a la función `get_top_processes_by_resource_usage`. Debe ser `get_top_processes_by_resource_usage(num_processes)`.

2. Se agregó `top_processes = get_top_processes_by_resource_usage(num_processes)` en la función `update_data` para obtener la lista de los procesos principales antes de iterar sobre ellos.

3. Se utilizó `plt.clf()` para limpiar el gráfico existente antes de dibujar uno nuevo en cada actualización de datos.

4. Se reemplazó `plt.savefig('usage_graph.png')` por `plt.pause(0.001)` para actualizar el gráfico en cada iteración sin guardar una imagen.

Con estas modificaciones, el código debería funcionar correctamente y mostrar las etiquetas, iniciar el monitoreo y actualizar los datos y gráficos de forma continua.
'''