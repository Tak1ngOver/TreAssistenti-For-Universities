import subprocess

server_process = subprocess.Popen(["python", "server.py"])
subprocess.run(["python", "main.py"])
server_process.terminate()