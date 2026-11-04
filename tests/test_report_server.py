from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

import serveReport


class ReportServerTests(unittest.TestCase):
    def test_only_report_is_exposed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'presentes-2026-11-04.html'
            report.write_text('<h1>Informe</h1>')
            (Path(directory) / '.env').write_text('DO_NOT_SERVE=this-is-a-test')
            with patch.object(serveReport, 'REPORT', report), patch.object(serveReport.ReportHandler, 'log_message'):
                server = ThreadingHTTPServer(('127.0.0.1', 0), serveReport.ReportHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f'http://127.0.0.1:{server.server_port}'
                try:
                    for path in ('/', '/presentes-2026-11-04.html'):
                        with urlopen(base + path, timeout=5) as response:
                            self.assertEqual(response.read(), b'<h1>Informe</h1>')
                            self.assertEqual(response.headers['Cache-Control'], 'no-store')
                    for path in ('/.env', '/../.env', '/%2e%2e/.env', '/CORRIDAS.md', '/reports/'):
                        with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                            urlopen(base + path, timeout=5)
                        self.assertEqual(error.exception.code, 404)
                        error.exception.close()
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)
