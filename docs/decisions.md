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
