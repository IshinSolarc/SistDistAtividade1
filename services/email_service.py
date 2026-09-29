import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

EMAILS = []


class EmailHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "email"})
            return

        if parsed.path == "/emails":
            self._send_json({"emails": EMAILS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/enviar":
            self._send_json({"mensagem": "Rota não encontrada"}, 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        assunto = dados.get("assunto", [""])[0].strip()
        destinatario = dados.get("destinatario", [""])[0].strip()
        mensagem = dados.get("mensagem", [""])[0].strip()

        if not assunto or not destinatario or not mensagem:
            self._send_json({"status": "erro", "mensagem": "Assunto, destinatário e mensagem são obrigatórios."}, 400)
            return

        email = {"assunto": assunto, "destinatario": destinatario, "mensagem": mensagem}
        EMAILS.append(email)
        print(f"[email] e-mail enviado com sucesso: destinatario={destinatario} | assunto={assunto}")
        self._send_json({"status": "ok", "mensagem": "E-mail enviado com sucesso.", "email": email})

    def _send_json(self, payload, status=200):
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8004), EmailHandler)
    print("API de e-mail rodando na porta 8004")
    server.serve_forever()
