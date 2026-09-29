import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PRODUTOS = [
    {"id": 1, "nome": "Notebook Gamer", "preco": 3200.00, "estoque": 5},
    {"id": 2, "nome": "Mouse Sem Fio", "preco": 150.00, "estoque": 20},
    {"id": 3, "nome": "Teclado Mecânico", "preco": 450.00, "estoque": 12},
]


class ProdutosHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "produtos"})
            return

        if parsed.path == "/produtos":
            print("[produtos] catálogo consultado com sucesso")
            self._send_json({"produtos": PRODUTOS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/produtos/baixar-estoque":
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            dados = parse_qs(body)

            if not dados:
                self._send_json({"status": "erro", "mensagem": "Dados não recebidos."}, 400)
                return

            produto_id = int(dados.get("produto_id", ["0"])[0])
            quantidade = int(dados.get("quantidade", ["0"])[0])

            produto = next((p for p in PRODUTOS if p["id"] == produto_id), None)
            if produto is None:
                self._send_json({"status": "erro", "mensagem": "Produto não encontrado."}, 404)
                return

            if quantidade <= 0:
                self._send_json({"status": "erro", "mensagem": "Quantidade inválida."}, 400)
                return

            if produto["estoque"] < quantidade:
                self._send_json({"status": "erro", "mensagem": "Estoque insuficiente."}, 400)
                return

            produto["estoque"] -= quantidade
            print(f"[produtos] estoque atualizado: produto={produto_id}, quantidade={quantidade}, restante={produto['estoque']}")
            self._send_json({"status": "ok", "mensagem": "Estoque atualizado.", "estoque_restante": produto["estoque"]})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

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
    server = ThreadingHTTPServer(("0.0.0.0", 8001), ProdutosHandler)
    print("API de produtos rodando na porta 8001")
    server.serve_forever()
