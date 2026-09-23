#!/usr/bin/env python3
"""
WSL2 to Windows Socket Bridge
Exposes Docker services (Grafana 3000, InfluxDB 8086) to Windows localhost via native WSL sockets.
"""

import socket
import threading
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [PortBridge] %(message)s")
logger = logging.getLogger("PortBridge")

FORWARD_PAIRS = [
    (3000, "127.0.0.1", 3000, "Grafana"),
    (8086, "127.0.0.1", 8086, "InfluxDB"),
]


def handle_client(client_socket, target_host, target_port):
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((target_host, target_port))
    except Exception as e:
        client_socket.close()
        return

    def forward(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            try:
                src.close()
            except Exception:
                pass
            try:
                dst.close()
            except Exception:
                pass

    t1 = threading.Thread(target=forward, args=(client_socket, remote_socket), daemon=True)
    t2 = threading.Thread(target=forward, args=(remote_socket, client_socket), daemon=True)
    t1.start()
    t2.start()


def start_forwarder(listen_port, target_host, target_port, name):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("0.0.0.0", listen_port))
        server.listen(100)
        logger.info(f"Port Bridge ativo: 0.0.0.0:{listen_port} -> {target_host}:{target_port} ({name})")
    except Exception as e:
        logger.warning(f"Nao foi possivel bindar 0.0.0.0:{listen_port} ({e}). Tentando porta alternativa...")
        return

    while True:
        try:
            client, addr = server.accept()
            threading.Thread(target=handle_client, args=(client, target_host, target_port), daemon=True).start()
        except Exception:
            break


def main():
    threads = []
    for lport, thost, tport, name in FORWARD_PAIRS:
        t = threading.Thread(target=start_forwarder, args=(lport, thost, tport, name), daemon=True)
        t.start()
        threads.append(t)

    logger.info("Todos os bridges WSL2 -> Windows estao ativos. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bridge encerrado.")


if __name__ == "__main__":
    main()
