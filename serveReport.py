"""Serve only the generated report on localhost, without exposing the repository."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

REPORT = Path(__file__).resolve().parent / 'reports/presentes-2026-11-04.html'


class ReportHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path not in ('/', '/' + REPORT.name):
            self.send_error(404)
            return
        content = REPORT.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not REPORT.is_file():
        parser.error('Build the report first: uv run --locked buildReport.py')
    with ThreadingHTTPServer(('127.0.0.1', args.port), ReportHandler) as server:
        print(f'Report: http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
