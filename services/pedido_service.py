import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PEDIDOS = [
    {"id": 1, "cliente": "Ana Souza", "produto": "Teclado Mecânico", "quantidade": 1},
    {"id": 2, "cliente": "João Silva", "produto": "Mouse Gamer", "quantidade": 2},
]


class PedidoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "pedidos"})
            return

        if parsed.path == "/pedidos":
            self._send_json({"pedidos": PEDIDOS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/pedidos":
            self._send_json({"mensagem": "Rota não encontrada"}, status=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        cliente = dados.get("cliente", [""])[0].strip()
        produto = dados.get("produto", [""])[0].strip()
        quantidade = dados.get("quantidade", ["0"])[0].strip()

        try:
            qtd = int(quantidade)
        except ValueError:
            self._send_json({"mensagem": "Quantidade inválida"}, status=400)
            return

        if not cliente or not produto or qtd <= 0:
            self._send_json({"mensagem": "Cliente, produto e quantidade são obrigatórios"}, status=400)
            return

        pedido = {"id": len(PEDIDOS) + 1, "cliente": cliente, "produto": produto, "quantidade": qtd}
        PEDIDOS.append(pedido)
        self._send_json({"mensagem": "Pedido cadastrado com sucesso", "pedido": pedido}, status=201)

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
    server = ThreadingHTTPServer(("0.0.0.0", 8003), PedidoHandler)
    print("Serviço de pedidos rodando na porta 8003")
    server.serve_forever()
