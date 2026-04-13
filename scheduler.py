import threading

# -------------------------------
# WORKER LIST (specialized)
# -------------------------------
pdf_workers = [("localhost", 5001)]   # PDF → TXT
txt_workers = [("localhost", 5002)]   # TXT → PDF

pdf_index = 0
txt_index = 0

lock = threading.Lock()


# -------------------------------
# SCHEDULER FUNCTION
# -------------------------------
def get_next_worker(filename, target_format):
    global pdf_index, txt_index

    with lock:
        # PDF → TXT
        if filename.endswith(".pdf") and target_format == "txt":
            worker = pdf_workers[pdf_index]
            pdf_index = (pdf_index + 1) % len(pdf_workers)
            return worker

        # TXT → PDF
        elif filename.endswith(".txt") and target_format == "pdf":
            worker = txt_workers[txt_index]
            txt_index = (txt_index + 1) % len(txt_workers)
            return worker

        else:
            raise ValueError("Unsupported conversion type")

    