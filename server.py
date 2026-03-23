import socket
import threading

from scheduler import get_next_worker

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
CHUNK_SIZE = 4096
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB safety limit

def _recv_exact(sock, num_bytes):
    buffer = b""
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            raise ConnectionError("Connection closed unexpectedly")
        buffer += packet
    return buffer

def stream_data(src_sock, dest_sock, total_bytes):
    remaining = total_bytes
    while remaining > 0:
        chunk = src_sock.recv(min(CHUNK_SIZE, remaining))
        if not chunk:
            raise ConnectionError("Stream interrupted")
        dest_sock.sendall(chunk)
        remaining -= len(chunk)


def relay_response(worker_sock, client_sock):
    size_bytes = _recv_exact(worker_sock, 8)
    result_size = int.from_bytes(size_bytes, "big")
    client_sock.sendall(size_bytes)
    stream_data(worker_sock, client_sock, result_size)


def handle_client(client_socket, address):
    print(f"\n[Server] Connected: {address}")
    worker_socket = None
    error_occurred = False

    try:
        client_socket.settimeout(30)

        name_len = int.from_bytes(_recv_exact(client_socket, 4), "big")
        if name_len <= 0 or name_len > 1024:
            raise ValueError("Invalid filename length")

        filename = _recv_exact(client_socket, name_len).decode("utf-8")
        print(f"[Server] File: {filename}")

        file_size = int.from_bytes(_recv_exact(client_socket, 8), "big")
        if file_size <= 0 or file_size > MAX_FILE_SIZE:
            raise ValueError("Invalid or too large file")
        print(f"[Server] Size: {file_size} bytes")

        worker_host, worker_port = get_next_worker()
        print(f"[Server] Dispatching → {worker_host}:{worker_port}")

        worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        worker_socket.settimeout(30)
        worker_socket.connect((worker_host, worker_port))

        worker_socket.sendall(name_len.to_bytes(4, "big"))
        worker_socket.sendall(filename.encode("utf-8"))
        worker_socket.sendall(file_size.to_bytes(8, "big"))

        stream_data(client_socket, worker_socket, file_size)
        print("[Server] File streamed to worker")

        relay_response(worker_socket, client_socket)
        print("[Server] Response sent to client")

    except Exception as e:
        print(f"[Server][ERROR] {address}: {e}")
        error_occurred = True
        try:
            client_socket.sendall((0).to_bytes(8, "big"))
            error_msg = str(e).encode("utf-8")
            client_socket.sendall(len(error_msg).to_bytes(4, "big"))
            client_socket.sendall(error_msg)
        except Exception as send_err:
            print(f"[Server][ERROR] Failed to send error feedback: {send_err}")

    finally:
        if worker_socket:
            worker_socket.close()
        client_socket.close()
        print(f"[Server] Closed connection: {address} "
              f"({'error' if error_occurred else 'success'})")


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print("=" * 55)
    print("  Distributed File Conversion Server (Streaming)")
    print("=" * 55)
    print(f"Listening on {HOST}:{PORT}\n")
    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    start_server()