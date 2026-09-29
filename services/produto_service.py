import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PRODUTOS = [
    {"id": 1, "nome": "Teclado Mecânico", "preco": 250.0},
    {"id": 2, "nome": "Mouse Gamer", "preco": 180.0},
]


class ProdutoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "produtos"})
            return

        if parsed.path == "/produtos":
            self._send_json({"produtos": PRODUTOS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/produtos":
            self._send_json({"mensagem": "Rota não encontrada"}, status=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        nome = dados.get("nome", [""])[0].strip()
        preco = dados.get("preco", ["0"])[0].strip()

        try:
            valor = float(preco)
        except ValueError:
            self._send_json({"mensagem": "Preço inválido"}, status=400)
            return

        if not nome:
            self._send_json({"mensagem": "Nome do produto é obrigatório"}, status=400)
            return

        produto = {"id": len(PRODUTOS) + 1, "nome": nome, "preco": valor}
        PRODUTOS.append(produto)
        self._send_json({"mensagem": "Produto cadastrado com sucesso", "produto": produto}, status=201)

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
    server = ThreadingHTTPServer(("0.0.0.0", 8002), ProdutoHandler)
    print("Serviço de produtos rodando na porta 8002")
    server.serve_forever()
