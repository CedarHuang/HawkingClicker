import psutil
import socket
import threading

import main_page

PORT_START = 45252
PORT_CNT = 3

PORTS = range(PORT_START, PORT_START + PORT_CNT)

def check():
    port = check_existing_instance()
    if port:
        try:
            wakeup_existing_instance(port)
        except:
            pass
        return False

    sock = create_socket()
    if sock is None:
        return False
    im_single_instance(sock)
    return True

def check_existing_instance():
    cur_p_name = psutil.Process().name()
    for conn in psutil.net_connections(kind='tcp4'):
        if conn.laddr.port in PORTS:
            try:
                p_name = psutil.Process(conn.pid).name()
                if p_name == cur_p_name:
                    return conn.laddr.port
            except:
                continue
    return 0

def create_socket():
    for port in PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.listen()
            return sock
        except:
            continue
    return None

def wakeup_existing_instance(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', port))
    sock.sendall(b'open')
    sock.close()

def im_single_instance(sock):
    def handle_connection():
        while True:
            conn, addr = sock.accept()
            data = conn.recv(1024)
            if data == b'open':
                main_page.root.deiconify()
            conn.close()
    threading.Thread(target=handle_connection, daemon=True).start()
