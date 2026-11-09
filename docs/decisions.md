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

## Ficha 03 — autenticação · authentication

- **JWT expira em 30 minutos e refresh em 1 dia; a SPA guarda ambos em memória** — evita persistir credenciais acessíveis a XSS em `localStorage`, aceitando novo login depois de recarregar a página; cookies `HttpOnly` exigiriam um endpoint de refresh adaptado. · Keep both tokens in memory to avoid XSS-readable storage, accepting re-login after reload.

### Matriz de autorização · authorization matrix

Todos os caminhos abaixo têm o prefixo `/api/v1`.

| Endpoint/operação | Anónimo | Cliente | Gestor |
| --- | --- | --- | --- |
| `GET /categories/` | 200 | 200 | 200 |
| `GET /products/` | 200 | 200 | 200 |
| `POST/PATCH/DELETE /products/` | 401 | 403 | 201/200/204 |
| `GET /customers/` e detalhe | 401 | 200 só perfil próprio; perfil alheio 404 | 200 todos |
| `POST /customers/` | 401 | 201 perfil próprio, se ainda não existir | 201 perfil do próprio gestor |
| `GET /orders/` e detalhe | 401 | 200 próprias; alheia 404 | 200 todas |
| `POST /orders/` | 401 | 201 própria (exige perfil Customer associado) | 201 própria (exige perfil associado) |
| `POST /orders/{id}/pay/` e `/cancel/` | 401 | 200/409 própria; alheia 404 | 200/409 todas |
| `GET /payments/` | 401 | 200 só pagamentos próprios | 200 todos |

- **O queryset de encomendas aplica o filtro por `customer__user` antes da permissão por objeto** — ao retirar esse filtro, o teste de lista passa a expor encomendas alheias e os testes parametrizados de detalhe e `pay` deixam de devolver 404 (a segunda camada responde 403); as duas camadas são necessárias para não confirmar a existência do recurso. · Queryset filtering hides foreign orders with 404; object permissions remain the second guard.

- **A leitura de categorias e produtos é pública, mas a escrita de produtos exige o grupo `gestores`** — a SPA pode mostrar o catálogo antes do login, sem abrir encomendas ou dados de clientes. · Let visitors browse the catalogue while restricting product writes and private resources.

### Ficha 03 — opção extra: audit log

- **Registamos `session_login`, `login_failed` e `jwt_login` como eventos de inserção, guardando só o identificador não secreto e `REMOTE_ADDR`** — passwords e tokens nunca entram no log; `user=SET_NULL` preserva o evento quando a conta é apagada. · Authentication audit events are insert-only and exclude credentials; `SET_NULL` preserves history.

## Ficha 04 — frontend · frontend

- **O frontend Vue fica em `frontend/` no mesmo repositório da API Django** — um repositório reúne aplicação, contrato OpenAPI e verificações do M2. · Keep the SPA and API together in the project repository.
- **Usamos CORS configurado no Django em vez de um proxy Vite** — o browser chama a origem explícita `http://localhost:8000`, exercitando a configuração CORS da Ficha 03. · Exercise the API's real CORS policy during local development.
- **Pesquisa e página vivem em `route.query`** — partilhar ou recarregar o URL preserva a vista; estado local isolado não teria esse comportamento. · URLs restore and share the current catalogue view.
- **O detalhe do produto é carregado por rota lazy** — o JavaScript dessa vista só é descarregado quando um produto é aberto. · Keep the initial catalogue bundle smaller.
- **O tipo `Product` espelha a API atual, sem `attributes`** — o domínio decidiu não incluir `JSONField`; a SPA mostra os campos realmente servidos pelo serializer. · Keep the frontend contract aligned with the relational API.
- **Geramos os tipos com `openapi-typescript` a partir de `schema.yaml` e usamos `openapi-fetch`** — os caminhos e filtros válidos acompanham o contrato publicado, em vez de duplicar tipos à mão. · Generate the frontend contract from the API schema.
- **A SPA mantém access e refresh apenas em memória e, ao receber 401, roda o refresh e repete o pedido uma vez** — segue a decisão da Ficha 03 e exige novo login após reload. · Follow the prior memory-only decision and retry once after token rotation.
- **Erros de login e encomenda são mostrados junto ao respetivo formulário/ação** — erros de validação e conflitos 409 não substituem a página inteira. · Keep API validation feedback beside the relevant action.
- **A pesquisa usa `useDebounce` com 300 ms antes de atualizar `route.query`** — evita um pedido por tecla e continua a preservar a pesquisa no URL para partilhar ou recarregar. · Debounce searches while keeping the URL as the source of navigable state.
- **A SPA mantém preços recebidos como strings e calcula a estimativa em cêntimos inteiros** — evita aritmética monetária com ponto flutuante; o backend calcula e confirma o total definitivo. · Keep money exact in minor units in the UI and authoritative in the API.
