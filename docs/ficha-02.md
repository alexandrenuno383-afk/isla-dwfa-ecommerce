# Ficha 02 — reflexão

1. `validate()` só corre nas escritas que passam pelo serializer; `QuerySet.update()`, scripts ou SQL podem contorná-lo. A `CheckConstraint` garante invariantes locais como quantidade positiva, enquanto stock, que está noutra tabela, exige ler o produto com `select_for_update()` dentro de uma transação para evitar vendas concorrentes acima do disponível.

2. Trocaria para `CursorPagination` num feed com muitas linhas e tráfego frequente: evita a contagem total e o custo crescente de `OFFSET`. O queryset precisa de ordenação determinística e estável; aqui pagamentos usam a chave única `-id`.
