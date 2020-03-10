import os, queue, threading
if os.name == "nt":
    import msvcrt, time
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
        return _listen_key_nt(timeout)
    elif os.name == "posix":
        return _listen_key_posix(timeout)

def _listen_key_posix(timeout):
    """
    listen to the keypress until it reaches timeout and returns pressed key.
    return type is str.
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

def _listen_key_nt(timeout):
    """
    listen to the keypress until it reaches timeout and returns pressed key.
    return type is str.
    returns None if nothing was pressed.
    """
    starttime = time.time()
    while True:
        if msvcrt.kbhit():
            try:
                return msvcrt.getch().decode()
            except UnicodeDecodeError:
                return None
        if time.time() - starttime >= timeout:
            return None