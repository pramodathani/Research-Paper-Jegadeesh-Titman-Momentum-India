"""Serves the companion page locally, because browsers block JSON from file://."""

import functools
import http.server
import socketserver
from pathlib import Path


class SiteServerApplication:
    """Serves the installed site/ folder on 127.0.0.1."""

    @classmethod
    def main(cls) -> None:
        """Starts the server on a free port and prints its address.

        Returns:
            None.
        """
        folder = Path(__file__).parent / 'site'
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=str(folder),
        )
        with socketserver.TCPServer(('127.0.0.1', 0), handler) as server:
            port = server.server_address[1]
            print(f'Serving the companion page at http://127.0.0.1:{port}/')
            server.serve_forever()


if __name__ == '__main__':
    SiteServerApplication.main()
