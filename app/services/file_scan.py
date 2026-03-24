import socket
import struct

from app.config import settings


class FileScanError(Exception):
    pass


class MalwareDetectedError(FileScanError):
    def __init__(self, signature: str):
        super().__init__(signature)
        self.signature = signature


def scan_bytes(data: bytes, filename: str = "upload") -> None:
    """Scan file bytes through clamd using the INSTREAM protocol."""
    if not settings.CLAMAV_ENABLED:
        return

    try:
        with socket.create_connection(
            (settings.CLAMAV_HOST, settings.CLAMAV_PORT),
            timeout=settings.CLAMAV_TIMEOUT_SECONDS,
        ) as sock:
            sock.sendall(b"zINSTREAM\0")
            chunk_size = 1024 * 1024
            for start in range(0, len(data), chunk_size):
                chunk = data[start:start + chunk_size]
                sock.sendall(struct.pack(">I", len(chunk)))
                sock.sendall(chunk)
            sock.sendall(struct.pack(">I", 0))

            response = b""
            while True:
                part = sock.recv(4096)
                if not part:
                    break
                response += part

        decoded = response.decode("utf-8", errors="replace").strip("\x00\r\n ")
        if decoded.endswith("FOUND"):
            signature = decoded.split(":", 1)[-1].replace("FOUND", "").strip()
            raise MalwareDetectedError(signature or "malware")
        if not decoded.endswith("OK"):
            raise FileScanError(
                f"Unexpected ClamAV response for {filename}: {decoded or 'empty response'}"
            )
    except MalwareDetectedError:
        raise
    except Exception as exc:
        raise FileScanError(f"ClamAV scan failed for {filename}: {exc}") from exc