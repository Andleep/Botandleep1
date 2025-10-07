import psutil
import time
import logging
from datetime import datetime

def monitor_system_resources():
    """مراقبة موارد النظام على Render"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    logging.info(f"📊 مراقبة الموارد | CPU: {cpu_percent}% | RAM: {memory.percent}% | Disk: {disk.percent}%")
    
    return {
        'timestamp': datetime.now(),
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent
    }
