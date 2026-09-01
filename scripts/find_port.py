"""Find a free local port (8511-8530), print it. Used by start.bat."""
import socket
import sys


def find_port(start: int = 8511, end: int = 8530) -> int:
    for port in range(start, end + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            s.close()
            continue
    sys.exit(f"no free port in {start}-{end}")


if __name__ == "__main__":
    print(find_port())
