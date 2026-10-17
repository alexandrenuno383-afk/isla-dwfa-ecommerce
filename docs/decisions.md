# Decisões · Decisions

PT: uma linha por decisão — o quê, porquê, alternativa rejeitada. Cresce ficha a ficha; o M1/M2/M3 avaliam este ficheiro.
EN: one line per decision — what, why, rejected alternative. Grows ficha by ficha; M1/M2/M3 grade this file.

## Esqueleto · Skeleton

- **`AUTH_USER_MODEL = "accounts.User"` desde o dia zero** — trocar depois da primeira migração obriga a reescrever o histórico; um `AbstractUser` vazio não custa nada. · Declared on day zero; swapping later means rewriting migration history; an empty `AbstractUser` is free.
- **Settings por ambiente (`base/dev/test/prod`) com `django-environ`** — o mesmo código em todos os ambientes, só as variáveis mudam (12-factor); segredos fora do git. · Same code everywhere, only env vars change; secrets stay out of git.
- **`/api/health/` devolve 503, não 500, com a base de dados em baixo** — é o código que um load balancer lê como "tira esta instância de rotação". · 503 is what a load balancer reads as "take this instance out of rotation".

## Ficha 02 — modelos · models

<!-- três decisões: um on_delete, uma constraint, JSONB sim/não · three decisions: one on_delete, one constraint, JSONB yes/no -->

- **`Product.category` usa `PROTECT` e `Order.customer` usa `PROTECT`** — categorias e clientes com histórico não desaparecem por uma eliminação acidental; categorias sem produtos e perfis sem encomendas continuam administráveis. · Historical references cannot disappear accidentally.
- **Preço e quantidade são validados na base de dados, e `(order, product)` é único** — a regra também vale para importações e outros caminhos que não passam pela API. · Database constraints cover every write path.
- **Não usamos `JSONField`** — os atributos do catálogo e da compra são relacionais e consultáveis; não há ainda requisitos de atributos variáveis que justifiquem JSONB. · Relational fields fit the known domain.
- **O índice composto em encomendas é `(status, -created_at)`** — suporta a listagem por estado ordenada pelas mais recentes, que é o fluxo principal da API. · Supports the main order list query.

## Ficha 02 — API

- **DRF com routers sob `/api/v1/` e OpenAPI via drf-spectacular** — recursos têm rotas consistentes e schema navegável em `/api/docs/`. · Consistent resource routing and discoverable API docs.
- **Listas de produtos usam `select_related(category)` e encomendas usam `select_related`/`prefetch_related`** — serializers podem expor relações sem consultas por linha. · Related fields are fetched in batches.
- **Criar encomendas valida stock e grava itens com preço congelado** — o preço do item representa o momento da compra e operações de stock/encomenda são atómicas. · Preserve purchase price and atomic stock updates.
- **`Order.total` é calculado com `annotate(Sum(quantity × unit_price))`** — evita persistir um total derivado que poderia divergir dos itens; o serializer expõe o resultado como somente leitura. · Compute rather than duplicate derived data.
- **`min_price` e `max_price` são filtros inclusivos** — o `FilterSet` mapeia-os a `price__gte` e `price__lte`, enquanto pesquisa e ordenação ficam limitadas a campos permitidos. · Explicit range filters and allowlisted ordering.
- **A ação `pay` usa MB WAY por omissão e só aceita encomendas pendentes** — pagamentos repetidos ou estados inválidos respondem HTTP 409; a regra e a transição ficam no serviço transacional. · State transitions live in a transactional service.
- **A lista de encomendas fica em até 3 queries com 20 resultados** — uma para a contagem da paginação, uma para encomendas/clientes/totais e uma para itens/produtos via `prefetch_related`; ver `test_order_list_with_nested_items_has_no_n_plus_one`. · Verified query budget for the nested list.
- **Categorias e pagamentos são só de leitura na API** — alterações de catálogo e criação de pagamentos ocorrem por fluxos controlados; a ação `pay` cria o pagamento correspondente. · Writes follow controlled workflows.
- **O schema OpenAPI gerado fica versionado em `schema.yaml` e a API permanece `AllowAny` nesta ficha** — a documentação fica reproduzível; autenticação e permissões foram deixadas para a Aula 04, conforme o enunciado. · Commit the generated contract and defer permissions to the next lesson.
