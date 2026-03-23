import socket

HOST = "localhost"
PORT = 8000  # whatever the server listens on

def send_file(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    filename = filepath.split("/")[-1]
    name_bytes = filename.encode("utf-8")
    name_len = len(name_bytes)
    file_size = len(data)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # send header
    sock.sendall(name_len.to_bytes(4, "big"))
    sock.sendall(name_bytes)
    sock.sendall(file_size.to_bytes(8, "big"))

    # send file
    sock.sendall(data)

    # receive response
    result_size = int.from_bytes(_recv_exact(sock, 8), "big")
    result = _recv_exact(sock, result_size)

    final_filename=filename.replace(".pdf",".txt")
    with open(final_filename,"w") as f:
        f.write(result.decode("utf-8"))

    print(f"Got result: {result_size} bytes")
    sock.close()

def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection dropped")
        buf += chunk
    return buf

send_file("test.pdf")