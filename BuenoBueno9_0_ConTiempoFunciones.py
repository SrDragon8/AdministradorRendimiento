import psutil
import pynvml
import wmi
import time

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
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
    gpu_usage = gpu_info.gpu
    return gpu_usage

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
    return memory_usage

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

    # Obtener el uso de GPU
    gpu_usage = get_gpu_usage()

    # Obtener los procesos por uso de CPU
    cpu_processes = sorted(psutil.process_iter(attrs=["pid", "name", "cpu_percent"]), key=lambda x: x.info["cpu_percent"], reverse=True)[:num_processes]
    for process in cpu_processes:
        pid = process.info["pid"]
        name = process.info["name"]
        cpu_usage = process.info["cpu_percent"]
        memory_usage = psutil.Process(pid).memory_percent()
        processes.append({
            "pid": pid,
            "name": name,
            "resource": "CPU",
            "usage": cpu_usage,
            "gpu_usage": gpu_usage,
            "memory_usage": memory_usage
        })
    
    # Obtener los procesos por uso de memoria RAM
    ram_processes = sorted(psutil.process_iter(attrs=["pid", "name", "memory_percent"]), key=lambda x: x.info["memory_percent"], reverse=True)[:num_processes]
    for process in ram_processes:
        pid = process.info["pid"]
        name = process.info["name"]
        cpu_usage = psutil.Process(pid).cpu_percent()
        memory_usage = process.info["memory_percent"]
        processes.append({
            "pid": pid,
            "name": name,
            "resource": "RAM",
            "usage": memory_usage,
            "gpu_usage": gpu_usage,
            "memory_usage": memory_usage
        })

    # Ordenar los procesos por el recurso utilizado
    processes = sorted(processes, key=lambda x: x["usage"], reverse=True)
    
    return processes[:num_processes]

# Tiempo total de ejecución en segundos
tiempo_total = 60
# Intervalo de tiempo entre cada lectura en segundos
intervalo = 20

# Ciclo de ejecución
num_lecturas = tiempo_total // intervalo
for i in range(num_lecturas):
    # Obtener y mostrar los datos
    cpu_usage = get_cpu_usage()
    cpu_temperature = get_cpu_temperature()
    cpu_model = get_cpu_model()
    gpu_usage = get_gpu_usage()
    gpu_temperature = get_gpu_temperature()
    gpu_model = get_gpu_model()
    memory_usage = get_memory_usage()
    storage_usage = get_storage_usage()
    network_usage = get_network_usage()

    print("Ronda de lectura", i+1)
    print("Uso de CPU:", round(cpu_usage, 1), "%")
    print("Temperatura del CPU:", round(cpu_temperature, 1), "°C")
    print("Modelo del CPU:", cpu_model)
    print("Uso de GPU:", round(gpu_usage, 1), "%")
    print("Temperatura de GPU:", round(gpu_temperature, 1), "°C")
    print("Modelo de GPU:", gpu_model)
    print("Uso de memoria:", round(memory_usage, 2), "%")
    print("Uso de almacenamiento:")
    for partition in storage_usage:
        print("Partición:", partition[0])
        print("Espacio usado:", round(partition[1] / (1024**3), 2), "GB")
        print("Espacio libre:", round(partition[2] / (1024**3), 2), "GB")
        print("Porcentaje de uso:", round(partition[3], 2), "%")
    print("Uso de red:", round(network_usage / (1024**2), 2), "MB")
    print("--------------------------------------")

    # Obtener y mostrar los principales 3 procesos que consumen recursos
    top_processes = get_top_processes_by_resource_usage(3)

    print("Principales procesos que consumen recursos:")
    for process in top_processes:
        print("Nombre:", process["name"])
        print("Recurso:", process["resource"])
        print("Uso de CPU:", round(process["usage"], 1), "%")
        print("Uso de GPU:", process["gpu_usage"], "%")
        print("Uso de RAM:", round(process["memory_usage"], 2), "%")
        print()

    print("--------------------------------------")

    # Esperar el intervalo de tiempo antes de la próxima lectura
    time.sleep(intervalo)
