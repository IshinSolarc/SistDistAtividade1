import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
INDEX_HTML = (ROOT / "index.html").read_text("utf-8")

PORTS = {
    "loja": 8000,
    "produtos": 8001,
    "cep": 8002,
    "fiscal": 8003,
    "email": 8004,
    "pagamento": 8005,
    "entrega": 8006,
}


def call_service(name, path, payload=None, method="GET"):
    url = f"http://localhost:{PORTS[name]}{path}"
    data = None
    headers = {}

    if payload is not None:
        if isinstance(payload, dict):
            data = urlencode(payload).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = payload

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except (HTTPError, URLError, ValueError) as exc:
        return {"status": "erro", "mensagem": f"Falha ao chamar {name}: {exc}"}


class LojaWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return

        if parsed.path == "/catalogo":
            resposta = call_service("produtos", "/produtos")
            self._send_json(resposta)
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/confirmar-compra":
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            dados = parse_qs(body)

            def valor(chave, padrao=""):
                return dados.get(chave, [padrao])[0].strip()

            nome = valor("nome")
            email = valor("email")
            produto_id = int(valor("produto_id", "1"))
            quantidade = int(valor("quantidade", "1"))
            cep = valor("cep")
            numero_cartao = valor("numero_cartao")

            if not nome or not email or not cep or not numero_cartao:
                self._send_json({"status": "erro", "mensagem": "Preencha nome, e-mail, CEP e cartão."}, 400)
                return

            catalogo = call_service("produtos", "/produtos")
            produto = None
            for item in catalogo.get("produtos", []):
                if item["id"] == produto_id:
                    produto = item
                    break

            if produto is None:
                self._send_json({"status": "erro", "mensagem": "Produto não encontrado."}, 404)
                return

            print(f"[loja] produto selecionado: {produto['nome']} | quantidade={quantidade}")
            total = produto["preco"] * quantidade

            baixa_estoque = call_service(
                "produtos",
                "/produtos/baixar-estoque",
                {"produto_id": str(produto_id), "quantidade": str(quantidade)},
                "POST",
            )

            if baixa_estoque.get("status") != "ok":
                self._send_json(baixa_estoque, 400)
                return

            print(f"[loja] estoque atualizado com sucesso para produto {produto_id}")

            endereco_cep = call_service("cep", f"/cep?valor={quote_plus(cep)}")
            if endereco_cep.get("status") != "ok":
                self._send_json({"status": "erro", "mensagem": "CEP inválido."}, 400)
                return

            print(f"[loja] endereço resolvido pelo CEP {cep}: {endereco_cep.get('endereco', {}).get('logradouro', '')}")
            dados_endereco = endereco_cep.get("endereco", {})
            endereco_entrega = (
                f"{dados_endereco.get('logradouro', '')}, {dados_endereco.get('bairro', '')}, "
                f"{dados_endereco.get('cidade', '')} - {dados_endereco.get('estado', '')}"
            ).replace(", ,", ",").strip(", ")

            pagamento = call_service(
                "pagamento",
                "/processar",
                {
                    "nome": nome,
                    "numero_cartao": numero_cartao,
                    "valor_total": str(total),
                },
                "POST",
            )

            if pagamento.get("status") != "ok":
                self._send_json(pagamento, 400)
                return

            print(f"[loja] pagamento aprovado: valor={total}")

            email_confirmacao = call_service(
                "email",
                "/enviar",
                {
                    "assunto": "Compra confirmada",
                    "destinatario": email,
                    "mensagem": f"Olá {nome}, sua compra do produto {produto['nome']} foi confirmada.",
                },
                "POST",
            )

            nota = call_service(
                "fiscal",
                "/emitir",
                {
                    "cliente": nome,
                    "email": email,
                    "produto": produto["nome"],
                    "quantidade": str(quantidade),
                    "valor_total": str(total),
                },
                "POST",
            )

            email_nota = call_service(
                "email",
                "/enviar",
                {
                    "assunto": "Nota fiscal",
                    "destinatario": email,
                    "mensagem": f"Sua nota fiscal foi emitida: {nota.get('numero_nota', 'NF-0001')}",
                },
                "POST",
            )

            print(f"[loja] nota fiscal emitida: {nota.get('numero_nota', 'NF-0001')}")

            entrega = call_service(
                "entrega",
                "/registrar",
                {
                    "cliente": nome,
                    "produto": produto["nome"],
                    "quantidade": str(quantidade),
                    "endereco": endereco_entrega,
                    "cep": cep,
                },
                "POST",
            )

            email_entrega = call_service(
                "email",
                "/enviar",
                {
                    "assunto": "Entrega",
                    "destinatario": email,
                    "mensagem": f"Seu pedido foi liberado para entrega. Código de rastreio: {entrega.get('codigo_rastreio', 'TRK-0001')}",
                },
                "POST",
            )

            print(f"[loja] entrega registrada com sucesso: {entrega.get('codigo_rastreio', 'TRK-0001')}")

            resposta = {
                "status": "ok",
                "mensagem": "Compra processada com sucesso.",
                "produto": produto["nome"],
                "quantidade": quantidade,
                "valor_total": total,
                "pagamento": pagamento,
                "nota": nota,
                "entrega": entrega,
                "email_confirmacao": email_confirmacao,
                "email_nota": email_nota,
                "email_entrega": email_entrega,
                "endereco_cep": endereco_cep,
            }
            print("[loja] compra concluída com sucesso")
            self._send_json(resposta)
            return

        self._send_json({"mensagem": "Rota não encontrada"}, 404)

    def _send_json(self, payload, status=200):
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _send_html(self, html_text):
        body = html_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORTS["loja"]), LojaWebHandler)
    print("Loja Web rodando na porta 8000")
    server.serve_forever()
