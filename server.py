import socket
import time
import logging
import ssl
from concurrent.futures import ThreadPoolExecutor

from scheduler import get_next_worker

# ================= CONFIG =================
HOST = "0.0.0.0"
PORT = 8000
CHUNK_SIZE = 4096
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_CLIENTS = 20
TIMEOUT = 30

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

# ================= HELPERS =================

def recv_exact(sock, num_bytes):
    buffer = b""
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            raise ConnectionError("Connection closed unexpectedly")
        buffer += packet
    return buffer


def stream_data(src, dest, total_bytes):
    transferred = 0
    start = time.time()

    while transferred < total_bytes:
        chunk = src.recv(min(CHUNK_SIZE, total_bytes - transferred))
        if not chunk:
            raise ConnectionError("Stream interrupted")
        dest.sendall(chunk)
        transferred += len(chunk)

    end = time.time()
    duration = end - start
    throughput = transferred / duration if duration > 0 else 0

    logging.info(f"Streamed {transferred} bytes in {duration:.2f}s | Throughput: {throughput:.2f} B/s")


def relay_response(worker_sock, client_sock):
    # receive output filename
    name_len = int.from_bytes(recv_exact(worker_sock, 4), "big")
    filename = recv_exact(worker_sock, name_len)

    client_sock.sendall(name_len.to_bytes(4, "big"))
    client_sock.sendall(filename)

    # receive file size
    size_bytes = recv_exact(worker_sock, 8)
    result_size = int.from_bytes(size_bytes, "big")

    client_sock.sendall(size_bytes)

    # stream file back
    stream_data(worker_sock, client_sock, result_size)


def send_error(client_sock, message):
    try:
        client_sock.sendall((0).to_bytes(8, "big"))
        encoded = message.encode("utf-8")
        client_sock.sendall(len(encoded).to_bytes(4, "big"))
        client_sock.sendall(encoded)
    except Exception as e:
        logging.error(f"Failed to send error: {e}")


# ================= CORE =================

def handle_client(client_socket, address):
    logging.info(f"Client connected: {address}")
    worker_socket = None
    start_time = time.time()

    try:
        client_socket.settimeout(TIMEOUT)

        # -------- RECEIVE METADATA --------
        name_len = int.from_bytes(recv_exact(client_socket, 4), "big")
        filename = recv_exact(client_socket, name_len).decode("utf-8")

        # TARGET FORMAT
        target_len = int.from_bytes(recv_exact(client_socket, 4), "big")
        target_format = recv_exact(client_socket, target_len).decode("utf-8")

        file_size = int.from_bytes(recv_exact(client_socket, 8), "big")

        if file_size <= 0 or file_size > MAX_FILE_SIZE:
            raise ValueError("Invalid file size")

        logging.info(f"File: {filename} | Target: {target_format} | Size: {file_size}")

        # -------- GET WORKER --------
        worker_host, worker_port = get_next_worker()
        logging.info(f"Dispatching to worker: {worker_host}:{worker_port}")

        # -------- CONNECT TO WORKER --------
        worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        worker_socket.settimeout(TIMEOUT)
        worker_socket.connect((worker_host, worker_port))

        # -------- SEND METADATA --------
        worker_socket.sendall(name_len.to_bytes(4, "big"))
        worker_socket.sendall(filename.encode("utf-8"))

        target_bytes = target_format.encode("utf-8")
        worker_socket.sendall(len(target_bytes).to_bytes(4, "big"))
        worker_socket.sendall(target_bytes)

        worker_socket.sendall(file_size.to_bytes(8, "big"))

        # -------- SEND FILE DATA (FIXED) --------
        file_data = recv_exact(client_socket, file_size)
        worker_socket.sendall(file_data)

        logging.info("File sent to worker")

        # -------- RELAY RESULT --------
        relay_response(worker_socket, client_socket)

        end_time = time.time()
        logging.info(f"Completed request in {end_time - start_time:.2f}s")

    except Exception as e:
        logging.error(f"Error with {address}: {e}")
        send_error(client_socket, str(e))

    finally:
        if worker_socket:
            worker_socket.close()
        client_socket.close()
        logging.info(f"Connection closed: {address}")


# ================= SERVER =================

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    logging.info("Server started")
    logging.info(f"Listening on {HOST}:{PORT}")

    # SSL SETUP
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    executor = ThreadPoolExecutor(max_workers=MAX_CLIENTS)

    while True:
        client_sock, addr = server_socket.accept()
        secure_sock = context.wrap_socket(client_sock, server_side=True)
        executor.submit(handle_client, secure_sock, addr)


if __name__ == "__main__":
    start_server()