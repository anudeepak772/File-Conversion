import socket
from reportlab.pdfgen import canvas
import io

HOST = "0.0.0.0"
PORT = 5002
CHUNK_SIZE = 4096


def _recv_exact(sock, num_bytes):
    buffer = b""
    while len(buffer) < num_bytes:
        packet = sock.recv(num_bytes - len(buffer))
        if not packet:
            raise ConnectionError("Connection closed unexpectedly")
        buffer += packet
    return buffer


# -------------------------------
# TXT → PDF (FIXED - NO REPEAT)
# -------------------------------
def txt_to_pdf(data):
    text = data.decode("utf-8")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    y = 800

    # ✅ ADD IMAGE 
    try:
        c.drawImage("sample.jpg", 50, y - 150, width=200, height=150)
        y -= 170
    except:
        print("Image not found, skipping...")

    # ✅ ONLY ONE LOOP (NO REPEAT)
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 20

        if y < 50:
            c.showPage()
            y = 800

    c.save()
    buffer.seek(0)

    return buffer.read()


# -------------------------------
# MAIN JOB HANDLER
# -------------------------------
def handle_job(client_socket):
    try:
        # filename
        name_len = int.from_bytes(_recv_exact(client_socket, 4), "big")
        filename = _recv_exact(client_socket, name_len).decode("utf-8")

        # target
        target_len = int.from_bytes(_recv_exact(client_socket, 4), "big")
        target_format = _recv_exact(client_socket, target_len).decode("utf-8")

        # size
        file_size = int.from_bytes(_recv_exact(client_socket, 8), "big")

        # data
        data = _recv_exact(client_socket, file_size)

        print(f"Received: {filename} → {target_format}")

        # -------------------------------
        # CONVERSION
        # -------------------------------
        if filename.endswith(".txt") and target_format == "pdf":
            result = txt_to_pdf(data)
            output_name = filename.replace(".txt", ".pdf")
        else:
            print("Unsupported conversion")
            client_socket.close()
            return

        # -------------------------------
        # SEND RESULT
        # -------------------------------
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


# -------------------------------
# START WORKER
# -------------------------------
def start_worker():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    print(f"TXT→PDF Worker listening on port {PORT}...")

    while True:
        client_socket, address = server_socket.accept()
        print(f"Connected from {address}")
        handle_job(client_socket)


if __name__ == "__main__":
    start_worker()