# ITAM to ITSM CMDB Automated Reconciliation Pipeline

Pipeline de automação e integração em **Python** desenvolvido para sincronizar dados de inventário de hardware e software (**ITAM** - Microsoft Intune, SCCM, Jamf) com o **CMDB** e o catálogo de serviços do **ITSM** (ServiceNow / BMC Helix).

Projeto desenhado seguindo padrões de governança **ITIL v4**, boas práticas de engenharia de software e resiliência de integrações corporativas.

---

##  Principais Funcionalidades

1. **Validação de Contratos de API (Pydantic):**
   * Tipagem estrita de payloads recebidos dos agentes de inventário.
   * Higienização de campos críticos (`serial_number`, `hostname`) e rejeição de registros corrompidos antes da gravação no CMDB.

2. **Reconciliação e Deduplicação (Pandas):**
   * Deduplicação de hardware utilizando a chave primária física (`serial_number`), mesmo que reportado por múltiplos agentes (ex: Intune + SCCM simultâneos).
   * Critério de desempate automatizado: preservação do registro com `last_checkin` mais recente.
   * Padronização de fabricantes (`DELL INC.`, `DELL` -> `Dell`).

3. **Ciclo de Vida do Ativo:**
   * Cálculo automatizado de inatividade: dispositivos sem contato há mais de 90 dias são categorizados como `Retired` / `Non-Operational`.

4. **Auditoria de Licenciamento (SAM - Software Asset Management):**
   * Identificação de ociosidade de licenças corporativas.
   * Abertura automática de chamados de revogação no ITSM para softwares não utilizados há mais de 60 dias.

5. **Resiliência e Tolerância a Falhas:**
   * Cliente HTTP (`httpx`) com **Exponential Backoff e Jitter** (`tenacity`).
   * Tratamento automático de **Rate Limits (HTTP 429)** e instabilidade de rede (HTTP 5xx).
   * Lógica de **Upsert (Find + Patch/Post)** para evitar CIs órfãos ou duplicados.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **HTTP / APIs:** `httpx`, `requests`
* **Validação de Dados:** `pydantic`
* **Data Processing & Normalização:** `pandas`
* **Resiliência:** `tenacity` (Exponential Backoff)
* **Testes:** `pytest`
* **Ambiente:** Compatível com AWS Lambda, Azure Functions ou agendamentos via Cron/Containers.

---

## 📂 Estrutura do Projeto

```bash
itam-itsm-sync/
├── src/
│   ├── schemas.py       # Modelos Pydantic (RawAsset e CMDB CI)
│   ├── normalizer.py    # Rotinas de deduplicação e limpeza com Pandas
│   ├── itsm_client.py   # Cliente ServiceNow/BMC com retry e backoff
│   └── main.py          # Orquestrador do pipeline de sincronização
├── tests/
│   └── test_pipeline.py # Testes unitários de validação e deduplicação
├── requirements.txt     # Dependências do projeto
└── README.md
```

---

## 🚀 Como Executar

### 1. Clonar e Instalar Dependências
```bash
git clone https://github.com/angelomarquess/itam-itsm-sync.git
cd itam-itsm-sync
python -m venv .venv
# Ativar venv (Windows):
.venv\Scripts\activate
# Instalar dependências:
pip install -r requirements.txt
```

### 2. Rodar a Demonstração do Pipeline
```bash
python -m src.main
```

### 3. Rodar os Testes Unitários
```bash
pytest tests/
```

---

## 👨‍💻 Autor
**Angelo Brito**  
*Analista de Sistemas / ITSM / Automação Python*  
LinkedIn: [angelo-brito-60896814](https://www.linkedin.com/in/angelo-brito-60896814/) • GitHub: [angelomarquess](http://github.com/angelomarquess)
