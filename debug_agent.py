import subprocess
import sys
import os
import time

# Iniciar agente con debugging
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
print(f"Data directory: {data_dir}")
print(f"Data directory exists: {os.path.exists(data_dir)}")
print(f"public.snmprec exists: {os.path.exists(os.path.join(data_dir, 'public.snmprec'))}")

command = [
    sys.executable,
    '-m', 'snmpsim.commands.responder',
    '--agent-udpv4-endpoint=127.0.0.1:16161',
    f'--data-dir={data_dir}',
    '--debug=all'
]

print(f"Command: {' '.join(command)}")
print("\nStarting agent with debug output...\n")

proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Read initial output
time.sleep(3)
if proc.poll() is not None:
    print("Agent terminated immediately!")
    output, _ = proc.communicate()
    print(output)
else:
    print(f"Agent running with PID: {proc.pid}")
    print("Press Ctrl+C to stop...")
    try:
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
