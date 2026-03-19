# Lead Intelligence

Biblioteca Python para **filtragem e qualificação de leads** com decisão comercial explícita (**accept** / **review** / **reject**) e **motivos** rastreáveis.

O foco inicial do produto é o nicho de **energia solar no Brasil**, com heurísticas opcionais em `solar.py` e análise de mensagem em `message_analysis.py`. O núcleo (`validator`, `analyzer`, `scorer`, `qualifier`) permanece **genérico e extensível**, sem LLM e sem APIs externas nesta versão.

## Decisão comercial

| Decisão   | Quando (resumo) |
|-----------|-----------------|
| `reject`  | Lead criticamente incompleto, sem canal de contato válido ou score muito baixo. |
| `review`  | Dados ou score intermediários, e-mail genérico, ou intenção ainda exploratória na mensagem. |
| `accept`  | Contato válido, completude e score altos, sinais alinhados com priorização comercial. |

Cada execução de `qualify_lead` devolve uma lista `reasons` em português para auditoria e produto.

## Estrutura do projeto

```
lead_intelligence/
  __init__.py
  validator.py         # E-mail, telefone, domínio genérico, contato, criticidade
  analyzer.py          # analyze_lead(lead) → lead + analysis
  scorer.py            # score_lead(lead) → 0..100
  qualifier.py         # qualify_lead(lead) → decision + reasons + solar + sinais da mensagem
  solar.py             # Heurísticas opcionais para solar (BR)
  message_analysis.py  # Sinais heurísticos em interest_message
tests/
  test_validator.py
  test_analyzer.py
  test_scorer.py
  test_qualifier.py
  test_solar.py
  test_message_analysis.py
  test_integration_lead_pipeline.py  # fluxo ponta a ponta (sem API)
pyproject.toml          # pacote instalável + extras [api] e [dev]
requirements.txt        # dependências da API FastAPI
requirements-dev.txt    # pytest + httpx + requirements.txt
LICENSE                 # MIT
```

## Clonar o repositório e instalar

```bash
git clone https://github.com/SEU_USUARIO/lead-intelligence.git
cd lead-intelligence
python -m venv .venv
.venv\Scripts\activate
```

**Só o toolkit (sem dependências externas):** o pacote `lead_intelligence` não exige pip extra para rodar `qualify_lead`.

**API + testes (recomendado para desenvolvimento):**

```bash
pip install -e ".[dev]"
```

Ou, equivalente:

```bash
pip install -r requirements-dev.txt
```

## Instalação (API apenas)

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Uso rápido

```python
from lead_intelligence.qualifier import qualify_lead

lead = {
    "name": "Ana",
    "company": "Loja Central",
    "email": "ana@lojacentral.com.br",
    "phone": "11987654321",
    "title": "Proprietária",
    "city": "Campinas",
    "state": "SP",
    "monthly_bill": 650,
    "property_type": "comercial",
    "ownership_status": "owned",
    "interest_message": "Preciso de orçamento para energia solar urgente.",
}

result = qualify_lead(lead)
# result["decision"]  → "accept" | "review" | "reject"
# result["score"]     → 0..100
# result["analysis"]  → completude, valid_email, etc.
# result["reasons"]   → lista de strings explicativas
# result["solar"]     → {"signals": {...}, "reasons": [...]}
# result["interest_signals"] → flags heurísticas da mensagem
```

Exemplo de saída (trecho):

```json
{
  "decision": "accept",
  "score": 100,
  "reasons": [
    "Imóvel próprio — melhor aderência típica para solar.",
    "Conta de luz relevante (>= R$ 250).",
    "Mensagem indica urgência ou pedido de orçamento.",
    "Contato válido, dados sólidos e score alto — priorizar contato comercial."
  ]
}
```

## Testes

```bash
pytest
# só integração do toolkit:
pytest tests/test_integration_lead_pipeline.py -v
```

## API FastAPI na web

- Variáveis: veja **`env.example`** e o guia **`DEPLOY.md`** (Render, Railway, Docker).
- **`CORS_ORIGINS`**: defina no host (ex.: `https://meuapp.com` ou `*` só para testes).
- **`LEADS_FILE`**: em produção, use disco persistente ou path absoluto para não perder `leads.jsonl` a cada deploy.

## Próximos passos (ideias)

- Integração com CRM / fila de outreach.
- Camada de regras configurável (YAML/JSON) por vertical.
- Modelo de linguagem **opcional** apenas como enriquecimento, mantendo heurísticas como fallback.
- Persistência e métricas (taxa accept/review/reject por canal).

## Licença

MIT
