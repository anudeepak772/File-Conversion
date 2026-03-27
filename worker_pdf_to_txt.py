import socket
import fitz

HOST = "0.0.0.0"
PORT = 5001


def _recv_exact(sock, num_bytes):
    buffer = b""
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            raise ConnectionError("Connection closed unexpectedly")
        buffer += packet
    return buffer


def pdf_to_txt(data):
    pdf = fitz.open(stream=data, filetype="pdf")
    text = ""

    for page in pdf:
        text += page.get_text()

    return text.encode("utf-8")


def handle_job(client_socket):
    try:
        name_len = int.from_bytes(_recv_exact(client_socket, 4), "big")
        filename = _recv_exact(client_socket, name_len).decode("utf-8")

        target_len = int.from_bytes(_recv_exact(client_socket, 4), "big")
        target_format = _recv_exact(client_socket, target_len).decode("utf-8")

        file_size = int.from_bytes(_recv_exact(client_socket, 8), "big")
        data = _recv_exact(client_socket, file_size)

        print(f"[PDF Worker] {filename} → {target_format}")

        if filename.endswith(".pdf") and target_format == "txt":
            result = pdf_to_txt(data)
            output_name = filename.replace(".pdf", ".txt")

            name_bytes = output_name.encode("utf-8")

            client_socket.sendall(len(name_bytes).to_bytes(4, "big"))
            client_socket.sendall(name_bytes)

            client_socket.sendall(len(result).to_bytes(8, "big"))
            client_socket.sendall(result)

            print(f"Sent: {output_name}")

    except Exception as e:
        print("Error:", e)

    finally:
        client_socket.close()


def start_worker():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    print(f"PDF → TXT Worker running on {PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        handle_job(client_socket)


start_worker()
