import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CLIENTES = [
    {"id": 1, "nome": "Ana Souza", "email": "ana@email.com"},
    {"id": 2, "nome": "João Silva", "email": "joao@email.com"},
]


class ClienteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "clientes"})
            return

        if parsed.path == "/clientes":
            self._send_json({"clientes": CLIENTES})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/clientes":
            self._send_json({"mensagem": "Rota não encontrada"}, status=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        nome = dados.get("nome", [""])[0].strip()
        email = dados.get("email", [""])[0].strip()

        if not nome or not email:
            self._send_json({"mensagem": "Nome e email são obrigatórios"}, status=400)
            return

        cliente = {"id": len(CLIENTES) + 1, "nome": nome, "email": email}
        CLIENTES.append(cliente)
        self._send_json({"mensagem": "Cliente cadastrado com sucesso", "cliente": cliente}, status=201)

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
    server = ThreadingHTTPServer(("0.0.0.0", 8001), ClienteHandler)
    print("Serviço de clientes rodando na porta 8001")
    server.serve_forever()
