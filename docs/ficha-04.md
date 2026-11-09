# Ficha 04 — reflexão

1. Remover o guard pode abrir a vista, mas sem token a API responde 401; com o token de outro cliente, só devolve as encomendas próprias e esconde as alheias com 404. A autenticação e as permissões no servidor protegem os dados; o guard melhora a navegação e evita mostrar uma vista privada antes do login.
2. O DRF envia `DecimalField` como string, por exemplo `"9.90"`, para preservar a representação decimal exata no JSON. Converter para `number` usa ponto flutuante binário, que não representa exatamente muitos decimais e pode introduzir erros de arredondamento ao somar valores. A aritmética definitiva do total deve viver no backend, usando `Decimal` e a precisão decimal da base de dados; a SPA só mostra uma estimativa, calculada em cêntimos inteiros.
