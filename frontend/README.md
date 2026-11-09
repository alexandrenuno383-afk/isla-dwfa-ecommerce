# Frontend — DWFA Store

SPA de catálogo para a API Django REST Framework deste repositório. Usa Vue 3, TypeScript, Vite, Vue Router, Pinia e Vitest.

## Preparar e arrancar

```sh
cp .env.example .env
npm install
npm run dev
```

O frontend abre em `http://localhost:5173`. A API deve estar disponível em `http://localhost:8000`; a origem Vite já consta em `CORS_ALLOWED_ORIGINS` por omissão nos settings Django. Se a API usar outra porta, atualize `VITE_API_URL` neste `.env` local.

Na raiz do repositório, a API pode ser iniciada com:

```sh
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py runserver
```

O comando `seed` cria 40 produtos de demonstração. A pesquisa `SKU-0000` encontra dez deles; a lista apresenta 20 resultados por página.

## Rotas e pesquisa

- `/` redireciona para `/products`.
- `/products` lista produtos, pesquisa por `search` com debounce de 300 ms e guarda pesquisa/página nos parâmetros do URL.
- `/products/:id` carrega o detalhe de forma lazy; `/products/99999` mostra o erro 404 vindo da API.
- `/login` autentica com JWT; `/orders` lista as encomendas do utilizador autenticado e permite pagar; `/orders/new` cria uma encomenda com vários produtos.
- Qualquer outro caminho mostra a vista 404 do frontend.

O utilizador de demonstração do seed é `ana`, com password `pass1234`; o seed cria dez encomendas de demonstração associadas a essa conta.

Os tokens ficam em memória, conforme a decisão da Ficha 03. A aplicação renova o access token e repete uma chamada uma vez quando recebe 401; o refresh token rodado substitui o anterior em memória. Por essa decisão, recarregar a página termina a sessão e exige novo login.

O OpenAPI gera `src/api/schema.d.ts` a partir de `../schema.yaml`. Depois de alterar a API, atualiza o schema na raiz com `uv run python manage.py spectacular --file schema.yaml` e regenera os tipos com `npm run generate:api`.

O modelo `Product` atual da API não tem `attributes` JSONB (a decisão da Ficha 02 foi não usar `JSONField`). O detalhe apresenta os campos existentes no contrato DRF: SKU, categoria, descrição, preço, stock e estado.

## Verificações

```sh
npm run type-check
npm run lint
npm run test:unit
npm run build
```
