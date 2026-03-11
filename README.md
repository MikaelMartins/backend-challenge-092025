# Backend Challenge — Sistema de Análise de Sentimentos (Python/FastAPI)

Implementação do endpoint `POST /analyze-feed` com análise determinística de sentimentos, influência, trending topics, flags especiais e detecção de anomalias.

## Quickstart (≤ 5 comandos)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoint

- Método: `POST`
- Rota: `/analyze-feed`
- Exemplo de payload: `examples/sample_request.json`

Exemplo de chamada:

```bash
curl -X POST 'http://localhost:8000/analyze-feed' \
  -H 'Content-Type: application/json' \
  -d @examples/sample_request.json
```

## CI (GitHub Actions)

Workflow criado em `.github/workflows/ci.yml` com 3 etapas principais:

1. `quality`: validação de dependências + compilação + smoke test de import
2. `unit-tests`: testes unitários (`tests/test_analyzer.py`) em matriz Python 3.11/3.12
3. `performance` (opt-in): teste de performance (`tests/test_performance.py`) via `workflow_dispatch` ou agendamento

## Checklist de Entrega — Status verificado

### Funcionalidade
- [x] Todos os 6 casos de teste passam
- [x] Endpoint HTTP funcional
- [x] Validações 400/422 implementadas
- [x] Função pura disponível para testes

### Performance
- [x] < 200ms para 1000 mensagens (opcional)
- [x] Uso de memória otimizado
- [x] Algoritmos O(n log n) ou melhor

### Qualidade
- [x] Código organizado e documentado
- [x] README com instruções claras (≤ 5 comandos)
- [x] Outputs determinísticos
- [x] Tratamento de edge cases

### Algoritmos
- [x] Tokenização/normalização NFKD
- [x] Janela temporal relativa ao timestamp da requisição
- [x] Ordem de precedência correta no sentimento
- [x] Flags MBRAS case-insensitive
- [x] Anomalias e trending implementados
- [x] SHA-256 determinístico para influência

### CI
- [x] Criação de um workflow do GitHub Actions
- [x] CI com ao menos 3 etapas

## Evidências rápidas

- Testes funcionais: `14 passed, 1 skipped`
- Performance: `1 passed` em `tests/test_performance.py` com `RUN_PERF=1`

## Estrutura do projeto

```text
.
├── main.py
├── sentiment_analyzer.py
├── schemas/request_schemas.py
├── tests/
│   ├── test_analyzer.py
│   └── test_performance.py
├── docs/
├── examples/
└── .github/workflows/ci.yml
```

