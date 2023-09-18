import time
import subprocess
import os
cmd = "nvidia-smi"
interval = 1
while True:
    ps = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    while True:
        data = ps.stdout.readline()
        data = str(data)
        if data == "b''":
            break
        if data.startswith('b\''):
            data = data[2:]
        if data.endswith('\\r\\n\''):
            data = data[:len(data)-5]
        data = data.replace('\\\\', '\\')
        print(data)
    print("\n\n\n\n\n\n\n")
    time.sleep(interval)
    os.system("cls")