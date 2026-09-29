import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ENTREGAS = []


class EntregaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "entrega"})
            return

        if parsed.path == "/entregas":
            self._send_json({"entregas": ENTREGAS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/registrar":
            self._send_json({"mensagem": "Rota não encontrada"}, 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        cliente = dados.get("cliente", [""])[0].strip()
        produto = dados.get("produto", [""])[0].strip()
        endereco = dados.get("endereco", [""])[0].strip()
        cep = dados.get("cep", [""])[0].strip()
        quantidade = int(dados.get("quantidade", ["1"])[0])

        if not cliente or not produto or not endereco or not cep:
            self._send_json({"status": "erro", "mensagem": "Dados de entrega incompletos."}, 400)
            return

        codigo = f"TRK-{len(ENTREGAS) + 1:04d}"
        entrega = {
            "codigo_rastreio": codigo,
            "cliente": cliente,
            "produto": produto,
            "quantidade": quantidade,
            "endereco": endereco,
            "cep": cep,
            "status": "disponibilizado para entrega",
        }
        ENTREGAS.append(entrega)
        print(f"[entrega] entrega registrada com sucesso: codigo={codigo} | cliente={cliente} | cep={cep}")
        self._send_json({"status": "ok", "mensagem": "Pedido disponibilizado para entrega.", "codigo_rastreio": codigo, "entrega": entrega})

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
    server = ThreadingHTTPServer(("0.0.0.0", 8006), EntregaHandler)
    print("API de entrega rodando na porta 8006")
    server.serve_forever()
