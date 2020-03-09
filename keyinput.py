import os, queue, threading
if os.name == "nt":
    raise OSError("Windows implementation hasn't been implemented yet")
elif os.name == "posix":
    import sys, tty, termios, select
else:
    raise OSError("Unknown OS type")

def listen_key(timeout = None):
    """
    Returns returned value of _listen_key_{os name}.
    type of the timeout should be integer.
    timeout value will be set to 0 if nothing were given.
    """
    if timeout == None:
        timeout = 0
    elif type(timeout) != int:
        raise ValueError("'timeout' argument only accepts integer value")
    if os.name == "nt":
        raise OSError("Windows implementation hasn't been implemented yet")
    elif os.name == "posix":
        return _listen_key_posix(timeout)

def _listen_key_posix(timeout):
    """
    listen to the keypress until it reaches timeout and returns pressed key.
    returns None if nothing was pressed.
    """
    oldsettings = termios.tcgetattr(sys.stdin.fileno())
    tty.setcbreak(sys.stdin)
    try:
        selresult = select.select([sys.stdin], [], [], timeout)
        isdata = selresult[0] != []
        if isdata:
            key = sys.stdin.read(1)
        else:
            key = None
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, oldsettings)
    return key

def get_key_queue():
    keyqueue = queue.Queue()
    if os.name == "nt":
        raise OSError("Windows implementation hasn't been implemented yet")
    elif os.name == "posix":
        threading.Thread(target = _get_key_queue_posix, args = (keyqueue,)).start()
    return keyqueue

def _get_key_queue_posix(queue):
    oldsettings = termios.tcgetattr(sys.stdin.fileno())
    tty.setcbreak(sys.stdin)
    try:
        while True:
            queue.put(sys.stdin.read(1))
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, oldsettings)