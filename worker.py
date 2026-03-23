import socket
import fitz

HOST = "0.0.0.0"
PORT = 5001
CHUNK_SIZE = 4096


def _recv_exact(sock, num_bytes):
    buffer = b""
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            raise ConnectionError("Connection closed unexpectedly")
        buffer += packet
    return buffer
def handle_job(client_socket):

    name_len=int.from_bytes(_recv_exact(client_socket,4),"big")
    filename=_recv_exact(client_socket,name_len).decode("utf-8")
    file_size=int.from_bytes(_recv_exact(client_socket,8),"big")

    data=_recv_exact(client_socket,file_size)

    pdf=fitz.open(stream=data, filetype="pdf")
    text=""
    for page in pdf:
        text=text+page.get_text()
    print(type(text))
    print(repr(text[:50]))
    result = text.encode("utf-8")
    result_size=len(result)
    client_socket.sendall(result_size.to_bytes(8,"big"))
    client_socket.sendall(result)
    client_socket.close()
def start_worker():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Worker listening on {PORT}")

    while True:
        client_socket, address = server_socket.accept()  # waits for server to connect
        handle_job(client_socket)

start_worker()


