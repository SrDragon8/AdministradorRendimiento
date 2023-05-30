import psutil
import pynvml

def get_gpu_usage():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
    gpu_usage = gpu_info.gpu
    pynvml.nvmlShutdown()
    return gpu_usage

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

# Obtener y mostrar los principales 3 procesos que consumen recursos en general
top_processes = get_top_processes_by_resource_usage(3)
print("Principales procesos que consumen recursos:")
for process in top_processes:
    print("Nombre:", process["name"])
    print("Recurso:", process["resource"])
    print("Uso de CPU:", process["usage"], "%")
    print("Uso de GPU:", process["gpu_usage"], "%")
    print("Uso de RAM:", process["memory_usage"], "%")
    print()
