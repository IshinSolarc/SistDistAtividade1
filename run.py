import subprocess
import sys
import time

PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8006]

SERVICES = [
    [sys.executable, "services/produtos_service.py"],
    [sys.executable, "services/cep_service.py"],
    [sys.executable, "services/fiscal_service.py"],
    [sys.executable, "services/email_service.py"],
    [sys.executable, "services/pagamento_service.py"],
    [sys.executable, "services/entrega_service.py"],
    [sys.executable, "loja_web.py"],
]

def main():
    processes = [subprocess.Popen(command) for command in SERVICES]
    print("Serviços do e-commerce iniciados.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait(timeout=5)
        print("Serviços encerrados.")


if __name__ == "__main__":
    main()
