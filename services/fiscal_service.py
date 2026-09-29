import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

NOTAS = []


class FiscalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "fiscal"})
            return

        if parsed.path == "/notas":
            self._send_json({"notas": NOTAS})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/emitir":
            self._send_json({"mensagem": "Rota não encontrada"}, 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        dados = parse_qs(body)

        cliente = dados.get("cliente", [""])[0].strip()
        email = dados.get("email", [""])[0].strip()
        produto = dados.get("produto", [""])[0].strip()
        quantidade = int(dados.get("quantidade", ["0"])[0])
        valor_total = float(dados.get("valor_total", ["0"])[0])

        if not cliente or not email or not produto:
            self._send_json({"status": "erro", "mensagem": "Dados da nota incompletos."}, 400)
            return

        numero_nota = f"NF-{len(NOTAS) + 1:04d}"
        nota = {
            "numero_nota": numero_nota,
            "cliente": cliente,
            "email": email,
            "produto": produto,
            "quantidade": quantidade,
            "valor_total": valor_total,
        }
        NOTAS.append(nota)
        print(f"[fiscal] nota emitida com sucesso: {numero_nota} | cliente={cliente} | valor={valor_total}")
        self._send_json({"status": "ok", "mensagem": "Nota fiscal emitida.", "numero_nota": numero_nota, "nota": nota})

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
    server = ThreadingHTTPServer(("0.0.0.0", 8003), FiscalHandler)
    print("API fiscal rodando na porta 8003")
    server.serve_forever()
