# Ficha 03 — Reflexão

1. **401** significa que faltam credenciais válidas; **403**, que o utilizador autenticado não tem permissão; **404**, que o recurso não existe no conjunto visível para esse utilizador.
   O `get_queryset()` filtra encomendas por `customer__user`, pelo que a encomenda alheia nem chega à verificação do objeto e o cliente recebe 404.
   O `has_object_permission` é uma segunda barreira; usar 404 oculta a existência da encomenda e evita revelar dados, sendo uma decisão de segurança deliberada.
2. `CORS_ALLOWED_ORIGINS` controla quais páginas em browsers podem ler respostas da API; não autentica pedidos nem impede `curl` ou scripts fora do browser de os enviar.
   Um cliente pode forjar o cabeçalho `Origin`; CORS não é firewall e, em alguns pedidos, o browser envia o pedido mas bloqueia o JavaScript de ler a resposta.
   O acesso indevido é impedido no servidor: JWT identifica o utilizador, `IsAuthenticated` exige login, permissões limitam ações por papel/objeto e os querysets ocultam dados alheios.
