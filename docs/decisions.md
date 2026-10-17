# Decisões · Decisions

PT: uma linha por decisão — o quê, porquê, alternativa rejeitada. Cresce ficha a ficha; o M1/M2/M3 avaliam este ficheiro.
EN: one line per decision — what, why, rejected alternative. Grows ficha by ficha; M1/M2/M3 grade this file.

## Esqueleto · Skeleton

- **`AUTH_USER_MODEL = "accounts.User"` desde o dia zero** — trocar depois da primeira migração obriga a reescrever o histórico; um `AbstractUser` vazio não custa nada. · Declared on day zero; swapping later means rewriting migration history; an empty `AbstractUser` is free.
- **Settings por ambiente (`base/dev/test/prod`) com `django-environ`** — o mesmo código em todos os ambientes, só as variáveis mudam (12-factor); segredos fora do git. · Same code everywhere, only env vars change; secrets stay out of git.
- **`/api/health/` devolve 503, não 500, com a base de dados em baixo** — é o código que um load balancer lê como "tira esta instância de rotação". · 503 is what a load balancer reads as "take this instance out of rotation".

## Ficha 02 — modelos · models

- **`Product.category` usa `PROTECT`** — impede apagar categorias que ainda têm produtos, preservando referências históricas. · Preserve referenced categories.
- **As constraints validam preço/quantidade positivos e unicidade de `(order, product)`; há ainda um índice `(status, -created_at)`** — invariantes e consulta principal ficam protegidos/otimizados na base de dados. · Enforce invariants and support order listing.
- **Não usamos `JSONField`** — o domínio atual é relacional e não tem atributos variáveis que justifiquem JSONB. · Keep queryable catalogue data relational.

## Ficha 02 — API

- **`OrderItem.unit_price` é somente de leitura** — o servidor copia o preço atual do produto ao criar o item e preserva o valor histórico. · The client cannot forge purchase prices.
- **Usamos `PageNumberPagination` nas listas gerais e `CursorPagination` em pagamentos** — com 20 encomendas/3 itens, medimos 3 queries com `prefetch_related`, 82 sem ele e 1 na lista cursor; o cursor evita `COUNT` e `OFFSET` caros em coleções grandes. · Measured: 3 vs 82 vs 1 queries.
- **A API é versionada no caminho (`/api/v1/`)** — alterações incompatíveis podem coexistir numa versão seguinte sem quebrar clientes existentes. · URL path versioning supports parallel API versions.

## Extensões opcionais · Optional extensions

- **Erros DRF usam Problem Details (`application/problem+json`, `about:blank`)** — `errors` mantém os detalhes de validação por campo sem alterar os status HTTP. · Keep field errors in a consistent envelope.
- **Só a ação `pay` recebe `ScopedRateThrottle` (30/min)** — limita operações de estado e mantém as listas de leitura livres nesta ficha. · Scope limits state-changing payment attempts.
- **A paginação cursor de pagamentos ordena por `-id`** — a chave única dá uma ordem estável ao cursor. · A unique key gives deterministic cursor ordering.
