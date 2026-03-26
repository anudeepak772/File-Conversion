import threading

workers=[("localhost",5001)]
current_worker=0
lock = threading.Lock()

def get_next_worker():
    global current_worker
    with lock:
        worker=workers[current_worker]
        current_worker=(current_worker+1)%len(workers)
        return worker


    