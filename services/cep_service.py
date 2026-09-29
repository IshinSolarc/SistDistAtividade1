import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CEPS = {
    "01001000": {"logradouro": "Praça da Sé", "bairro": "Sé", "cidade": "São Paulo", "estado": "SP"},
    "01310930": {"logradouro": "Avenida Paulista", "bairro": "Bela Vista", "cidade": "São Paulo", "estado": "SP"},
    "30130010": {"logradouro": "Rua da Bahia", "bairro": "Centro", "cidade": "Belo Horizonte", "estado": "MG"},
}


class CEPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "cep"})
            return

        if parsed.path == "/cep":
            params = parse_qs(parsed.query)
            cep = params.get("valor", [""])[0].strip()
            endereco = CEPS.get(cep, None)
            if not endereco:
                self._send_json({"status": "erro", "mensagem": "CEP não encontrado."}, 404)
                return
            print(f"[cep] CEP consultado com sucesso: {cep}")
            self._send_json({"status": "ok", "cep": cep, "endereco": endereco})
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/cep":
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            dados = parse_qs(body)
            cep = dados.get("valor", [""])[0].strip()
            endereco = CEPS.get(cep)
            if not endereco:
                self._send_json({"status": "erro", "mensagem": "CEP não encontrado."}, 404)
                return
            print(f"[cep] CEP recebido via POST com sucesso: {cep}")
            self._send_json({"status": "ok", "cep": cep, "endereco": endereco})
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
    server = ThreadingHTTPServer(("0.0.0.0", 8002), CEPHandler)
    print("API de CEP rodando na porta 8002")
    server.serve_forever()
