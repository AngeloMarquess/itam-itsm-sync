import logging
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import Dict, Any, Optional
from src.schemas import CMDBConfigurationItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
logger = logging.getLogger("ITSMClient")

class ServiceNowClient:
    """
    Cliente de integração com ITSM (ServiceNow Table API / IRE) com resiliência:
    - Exponential Backoff em erros 429 (Rate Limit) e 5xx (Instabilidade)
    - Busca antes de inserir para evitar CIs órfãos ou duplicados
    """

    def __init__(self, instance_url: str, username: str = "", password: str = "", token: str = ""):
        self.instance_url = instance_url.rstrip("/")
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.auth = (username, password) if username and password else None

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=20),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        reraise=True
    )
    def _execute_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        url = f"{self.instance_url}{endpoint}"
        with httpx.Client(auth=self.auth, headers=self.headers, timeout=15.0) as client:
            response = client.request(method, url, **kwargs)
            if response.status_code == 429:
                logger.warning("Rate limit 429 retornado pela API do ITSM. Acionando Exponential Backoff...")
                response.raise_for_status()
            if response.status_code >= 500:
                logger.error(f"Erro no servidor ITSM: {response.status_code}. Tentando novamente...")
                response.raise_for_status()
            return response

    def find_ci_by_serial(self, table_name: str, serial_number: str) -> Optional[Dict[str, Any]]:
        """
        Consulta o CMDB para verificar se o CI já existe através do serial_number.
        """
        endpoint = f"/api/now/table/{table_name}?sysparm_query=serial_number={serial_number}&sysparm_limit=1"
        try:
            resp = self._execute_request("GET", endpoint)
            if resp.status_code == 200:
                results = resp.json().get("result", [])
                if results:
                    return results[0]
        except Exception as e:
            logger.error(f"Falha ao consultar CI por serial {serial_number}: {e}")
        return None

    def upsert_ci(self, table_name: str, ci_data: CMDBConfigurationItem) -> Dict[str, Any]:
        """
        Aplica a lógica de Reconciliação (Upsert):
        - Se existe CI com o serial_number, faz PATCH (Update).
        - Se não existe, faz POST (Create).
        """
        existing_ci = self.find_ci_by_serial(table_name, ci_data.serial_number)
        payload = ci_data.model_dump(exclude_none=True)

        if existing_ci and "sys_id" in existing_ci:
            sys_id = existing_ci["sys_id"]
            endpoint = f"/api/now/table/{table_name}/{sys_id}"
            logger.info(f"Atualizando CI existente '{ci_data.name}' (sys_id: {sys_id})...")
            resp = self._execute_request("PATCH", endpoint, json=payload)
        else:
            endpoint = f"/api/now/table/{table_name}"
            logger.info(f"Criando novo CI no CMDB para '{ci_data.name}' (Serial: {ci_data.serial_number})...")
            resp = self._execute_request("POST", endpoint, json=payload)

        return resp.json() if resp.status_code in [200, 201] else {}

    def create_license_revocation_ticket(self, user_email: str, software_name: str, idle_days: int) -> Dict[str, Any]:
        """
        Rotina SAM: Abre requisição automática para revogação de software ocioso.
        """
        endpoint = "/api/now/table/sc_request"
        payload = {
            "short_description": f"Auditoria SAM: Revogação de Licença {software_name}",
            "description": f"O usuário {user_email} não utiliza o software {software_name} há {idle_days} dias. Revogação solicitada automaticamente para otimização de custos.",
            "urgency": "3",
            "impact": "3"
        }
        logger.info(f"Abrindo chamado automático de revogação para {user_email}...")
        resp = self._execute_request("POST", endpoint, json=payload)
        return resp.json()
