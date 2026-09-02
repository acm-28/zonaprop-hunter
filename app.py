import os
from http.server import BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

def get_html_content() -> bytes:
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "rb") as f:
            return f.read()
    alt_file = os.path.join(BASE_DIR, "output", "zonaprop_oportunidades.html")
    if os.path.exists(alt_file):
        with open(alt_file, "rb") as f:
            return f.read()
    return b"<h1>Zonaprop Hunter CABA</h1><p>El reporte se esta generando...</p>"

# WSGI entrypoint for Vercel
def app(environ, start_response):
    status = "200 OK"
    response_headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Cache-Control", "public, max-age=0, must-revalidate")
    ]
    start_response(status, response_headers)
    return [get_html_content()]

# Standard HTTP Serverless Handler for Vercel
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = get_html_content()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "public, max-age=0, must-revalidate")
        self.end_headers()
        self.wfile.write(content)
