# isla-dwfa-ecommerce — esqueleto do projeto · project skeleton

**Desenvolvimento Web Full-stack Avançado** · Mestrado em Engenharia Informática · ISLA Gaia · 2026/27 · David Vaz ([@davidmgvaz](https://github.com/davidmgvaz))

**PT** — Projeto da UC com o domínio de e-commerce da Ficha 02 e autenticação, autorização e hardening da API da Ficha 03. Inclui PostgreSQL 16 em Docker, Django REST Framework, JWT, documentação OpenAPI, testes com pytest-django, factory_boy, ruff e CI.
**EN** — Course project with the Ficha 02 e-commerce domain and the Ficha 03 API authentication, authorization and hardening. It includes PostgreSQL 16 in Docker, Django REST Framework, JWT, OpenAPI documentation, pytest-django tests, factory_boy, ruff and CI.

## Começar · Getting started

**Ficha 02 e Ficha 03 são trabalho individual** · both are individual assignments: cada aluno mantém o seu próprio fork privado, partilhado com `davidmgvaz`; os pares são para o Projeto M1–M3 · each student keeps a private fork shared with `davidmgvaz`; pairs are for the M1–M3 project.

```sh
git clone git@github.com:<vosso-utilizador>/isla-dwfa-ecommerce.git
cd isla-dwfa-ecommerce
cp .env.example .env                 # nunca commitar o .env · never commit .env
docker compose up -d                 # PostgreSQL 16 → docker compose ps mostra "healthy"
uv sync                              # .venv com Django + dependências de dev
uv run python manage.py migrate
uv run pytest --create-db            # cria uma BD de testes nova e corre a suite
uv run python manage.py seed         # catálogo e cliente de demonstração, idempotente
uv run python manage.py createsuperuser  # opcional, para usar o Django Admin
uv run python manage.py runserver    # health, /api/v1/ e /admin/
```

Requisitos · requirements: Python 3.13, [uv](https://docs.astral.sh/uv/), Docker Compose v2, Git. **Porta 5432 ocupada?** · port busy? → `ports: ["5433:5432"]` no `compose.yaml` **e** `:5433` no `DATABASE_URL` do `.env`.

## O que está cá · What is here

```
config/settings/
  base.py      tudo o que é partilhado · everything shared (lê .env via django-environ)
  dev.py       DEBUG, email na consola · console email
  test.py      hasher rápido, email em memória · fast hasher, in-memory email
  prod.py      cabeçalhos de segurança, sem DEBUG · security headers, no DEBUG
accounts/      User, AuditEvent, login JWT e GET /api/v1/me/ · JWT login and current user
core/          GET /api/health/ → 200 {"status":"ok","db":"ok"} · 503 com a BD em baixo · 503 when the DB is down
shop/          Category, Product, Customer, Order, OrderItem, Payment · models, API, factories, seed
docs/decisions.md   as vossas decisões, uma linha cada · your decisions, one line each
compose.yaml   PostgreSQL 16 com healthcheck
pytest.ini     DJANGO_SETTINGS_MODULE=config.settings.test · --reuse-db
.github/workflows/ci.yml   ruff + makemigrations --check + pytest, com PostgreSQL de serviço
```

`DJANGO_SETTINGS_MODULE` vem do `.env` (`config.settings.dev`); os testes usam `config.settings.test` (ver `pytest.ini`); `wsgi.py`/`asgi.py` assumem `config.settings.prod`.

## API e autenticação · API and authentication

- Recursos CRUD em `/api/v1/categories/`, `products/`, `customers/`, `orders/` e `payments/`.
- A lista de produtos aceita `category`, `is_active`, `search` e `ordering`; listas usam paginação por página (20 resultados).
- Encomendas aceitam itens na criação, verificam stock e guardam o preço unitário da compra. `POST /api/v1/orders/{id}/cancel/` cancela uma encomenda pendente e repõe o stock.
- Schema OpenAPI: `/api/schema/`; interface Swagger: `/api/docs/`.
- Seed de demonstração repetível: `uv run python manage.py seed`.
- As leituras de categorias e produtos são públicas; as escritas de produtos exigem o grupo `gestores`. Os restantes recursos requerem autenticação. Clientes só veem as próprias encomendas e pagamentos; gestores podem consultar todos os registos.
- Login e refresh JWT: `POST /api/v1/auth/token/` e `POST /api/v1/auth/token/refresh/`. Usar o token de acesso em `Authorization: Bearer <access>`; `GET /api/v1/me/` devolve o utilizador autenticado e os seus grupos.
- Tokens de acesso duram 30 minutos e refresh 1 dia. O refresh roda e invalida o token anterior. O login tem limite de 10 tentativas por minuto.
- CORS permite por omissão `http://localhost:5173` apenas nos caminhos `/api/`; configure origens adicionais em `CORS_ALLOWED_ORIGINS` no `.env`.
- A opção extra implementada é o audit log: regista logins de sessão e JWT e falhas de autenticação, sem guardar passwords ou tokens.

### Exemplo de login · login example

```sh
curl -sS -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"O_TEU_UTILIZADOR","password":"A_TUA_PASSWORD"}'

curl -sS http://localhost:8000/api/v1/me/ \
  -H 'Authorization: Bearer O_TEU_ACCESS_TOKEN'
```

Não coloques passwords, tokens ou o ficheiro `.env` no repositório.

## Ficha 03 — segurança · security

- A autenticação padrão é JWT, seguida de sessão para manter o Django Admin e a Browsable API funcionais; a permissão padrão é `IsAuthenticated`.
- `CategoryViewSet` permite leitura pública. Produtos podem ser lidos por utilizadores autenticados e só o grupo `gestores` pode criar, alterar ou apagar produtos.
- Encomendas e pagamentos são filtrados por proprietário no queryset e protegidos por permissões por objeto. Um cliente que tenta consultar ou pagar a encomenda de outra pessoa recebe 404.
- `customer`, `status` e `total` são somente de leitura na criação/alteração de encomendas. O cliente associado é definido pelo servidor com base no utilizador autenticado.
- Passwords novas usam Argon2, com PBKDF2 para verificar hashes existentes. A password mínima tem 12 caracteres.
- O modelo `AuditEvent` é preenchido por inserções nos sinais de autenticação e no serializer JWT. As falhas guardam apenas o identificador fornecido, nunca a password.

Para recriar a base de dados de testes quando as migrações mudarem (o pytest está configurado com `--reuse-db`):

```sh
uv run pytest --create-db
```

Verificações de qualidade e produção:

```sh
uv run ruff check .
uv run ruff format --check .
uv run python manage.py makemigrations --check --dry-run
uv run pytest

DJANGO_SETTINGS_MODULE=config.settings.prod \
SECRET_KEY='temporary-review-key-0123456789abcdefghijklmnopqrstuvwxyz-0123456789' \
ALLOWED_HOSTS=shop.example \
DATABASE_URL=postgres://x@x/x \
uv run python manage.py check --deploy
```

O `SECRET_KEY` acima é apenas um valor temporário para a verificação; em produção, define um segredo forte através do ambiente. Não guardes segredos no Git.

## Comandos do dia a dia · Everyday commands

```sh
uv run ruff check . && uv run ruff format .      # lint + formato (o CI falha sem isto · CI fails without it)
uv run python manage.py makemigrations shop --name initial_domain
uv run python manage.py sqlmigrate shop 0001     # ler o SQL antes de aplicar · read the SQL before applying
uv run python manage.py migrate
uv run pytest -x                                 # parar no primeiro erro · stop at first failure
docker compose exec db psql -U dwfa              # \dt · \d+ shop_order
docker compose down -v                           # apagar a base de dados local · wipe the local DB
```

## Regras que ficam para o semestre · Rules for the whole semester

- Segredos nunca no git: `.env` ignorado, `.env.example` commitado com valores fictícios · secrets never in git.
- Modelos referem o utilizador via `settings.AUTH_USER_MODEL`, nunca `User` diretamente · never import `User` directly.
- Migrações commitadas e lidas (`sqlmigrate`) antes de aplicadas · migrations committed and read before applied.
- Sem N+1 nos endpoints de lista; `django_assert_num_queries` nos testes · no N+1 on list endpoints.
- Decisões em `docs/decisions.md`, uma linha cada · decisions in `docs/decisions.md`, one line each.

## Entregas · Deliverables

Ficha 02 · tags `ficha-02-models` e `ficha-02-api` · Ficha 03 · tag `ficha-03` · submeter o URL do repositório no Moodle conforme o prazo indicado na ficha · M1 09/11 · M2 29/11 · M3 03/01.
