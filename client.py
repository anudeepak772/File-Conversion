import socket
import ssl

HOST = "localhost" 
PORT = 8000


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection dropped")
        buf += chunk
    return buf


def send_file(filepath, target_format):
    # read file
    with open(filepath, "rb") as f:
        data = f.read()

    filename = filepath.split("/")[-1]
    name_bytes = filename.encode("utf-8")
    name_len = len(name_bytes)

    target_bytes = target_format.encode("utf-8")
    target_len = len(target_bytes)

    file_size = len(data)

    # -------------------------------
    # SSL CONNECTION
    # -------------------------------
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = context.wrap_socket(sock, server_hostname="localhost")
    sock.connect((HOST, PORT))

    # -------------------------------
    # SEND TO SERVER
    # -------------------------------
    sock.sendall(name_len.to_bytes(4, "big"))
    sock.sendall(name_bytes)

    sock.sendall(target_len.to_bytes(4, "big"))
    sock.sendall(target_bytes)

    sock.sendall(file_size.to_bytes(8, "big"))
    sock.sendall(data)

    # -------------------------------
    # RECEIVE FROM SERVER
    # -------------------------------

    # output filename
    out_name_len = int.from_bytes(_recv_exact(sock, 4), "big")
    out_filename = _recv_exact(sock, out_name_len).decode("utf-8")

    # file size
    result_size = int.from_bytes(_recv_exact(sock, 8), "big")
    result = _recv_exact(sock, result_size)

    # save output
    with open(out_filename, "wb") as f:
        f.write(result)

    print(f"Received: {out_filename} ({result_size} bytes)")

    sock.close()


# -------------------------------
# RUN
# -------------------------------
file = input("Enter file name: ")
target = input("Convert to (txt/pdf): ")

send_file(file, target)
