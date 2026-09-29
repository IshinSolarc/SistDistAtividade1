import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TRANSACOES = []


class PagamentoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "pagamento"})
            return

        if parsed.path == "/transacoes":
            self._send_json({"transacoes": TRANSACOES})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/processar":
            self._send_json({"mensagem": "Rota não encontrada"}, 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        nome = dados.get("nome", [""])[0].strip()
        numero_cartao = dados.get("numero_cartao", [""])[0].strip()
        valor_total = float(dados.get("valor_total", ["0"])[0])

        if not nome or not numero_cartao or valor_total <= 0:
            self._send_json({"status": "erro", "mensagem": "Dados de pagamento incompletos."}, 400)
            return

        transacao = {
            "id": len(TRANSACOES) + 1,
            "nome": nome,
            "numero_cartao": numero_cartao,
            "valor_total": valor_total,
            "status": "aprovado",
        }
        TRANSACOES.append(transacao)
        print(f"[pagamento] transação aprovada: id={transacao['id']} | valor={valor_total} | cliente={nome}")
        self._send_json({"status": "ok", "mensagem": "Pagamento aprovado.", "transacao": transacao})

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
    server = ThreadingHTTPServer(("0.0.0.0", 8005), PagamentoHandler)
    print("API de pagamento rodando na porta 8005")
    server.serve_forever()
