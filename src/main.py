import json
import logging
from datetime import datetime
from src.schemas import RawDeviceAsset
from src.normalizer import reconcile_and_normalize
from src.itsm_client import ServiceNowClient

logger = logging.getLogger("PipelineRunner")

# Dados simulando resposta bruta de inventário de ferramentas como Intune/Jamf/SCCM
MOCK_RAW_INVENTORY = [
    {
        "device_id": "INTUNE-001",
        "serial_number": "BRG9821XYZ",
        "hostname": "SP-NOTE-0142",
        "manufacturer": "DELL INC.",
        "model": "Latitude 5420",
        "os_name": "Windows 11 Enterprise",
        "os_version": "22H2",
        "assigned_user_email": "colaborador1@empresa.com",
        "last_checkin": "2026-09-28T14:30:00",
        "idle_days_license": 12
    },
    {
        # Registro duplicado (ex: SCCM e Intune reportando a mesma máquina com datas diferentes)
        "device_id": "SCCM-994",
        "serial_number": "BRG9821XYZ",
        "hostname": "sp-note-0142",
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "os_name": "Windows 11 Enterprise",
        "os_version": "22H2",
        "assigned_user_email": "colaborador1@empresa.com",
        "last_checkin": "2026-09-30T10:00:00",  # Mais recente -> deve prevalecer
        "idle_days_license": 12
    },
    {
        "device_id": "JAMF-551",
        "serial_number": "C02G8712MD6R",
        "hostname": "macbook-design-01",
        "manufacturer": "APPLE INC.",
        "model": "MacBook Pro 16",
        "os_name": "macOS Sonoma",
        "os_version": "14.4",
        "assigned_user_email": "designer@empresa.com",
        "last_checkin": "2026-09-29T18:15:00",
        "idle_days_license": 75  # Mais de 60 dias ocioso -> dispara SAM
    },
    {
        # Ativo antigo inativo há mais de 100 dias (deve virar Retired)
        "device_id": "INTUNE-882",
        "serial_number": "5CD8239ABC",
        "hostname": "hp-financeiro-old",
        "manufacturer": "HEWLETT-PACKARD",
        "model": "EliteBook 840 G5",
        "os_name": "Windows 10 Pro",
        "os_version": "21H1",
        "assigned_user_email": None,
        "last_checkin": "2026-05-10T08:00:00",
        "idle_days_license": 0
    }
]

def run_sync_pipeline(mock_itsm: bool = True):
    print("=" * 60)
    print("INICIANDO PIPELINE DE AUTOMAÇÃO ITAM -> ITSM / CMDB")
    print("=" * 60)

    # 1. Validação de Contrato de Entrada (Pydantic)
    print(f"\n[Passo 1] Validando {len(MOCK_RAW_INVENTORY)} registros brutos com Pydantic...")
    validated_raw = []
    for item in MOCK_RAW_INVENTORY:
        asset = RawDeviceAsset(**item)
        validated_raw.append(asset.model_dump())
    print(" Todos os contratos validados com sucesso.")

    # 2. Reconciliação, Limpeza e Deduplicação (Pandas)
    print("\n[Passo 2] Executando Reconciliação e Deduplicação com Pandas...")
    cis = reconcile_and_normalize(validated_raw)
    print(f" Registros após deduplicação de hardware: {len(cis)} CIs únicos prontos para o CMDB.")

    for ci in cis:
        print(f"   -> CI: {ci.name} | Serial: {ci.serial_number} | Fabricante: {ci.manufacturer} | Status: {ci.install_status}")

    # 3. Auditoria de Licenças Ociosas (SAM)
    print("\n[Passo 3] Executando Auditoria de Software Asset Management (SAM)...")
    for raw in validated_raw:
        if raw["idle_days_license"] >= 60 and raw["assigned_user_email"]:
            print(f"  [ALERTA SAM] Software ocioso detectado há {raw['idle_days_license']} dias para {raw['assigned_user_email']}!")
            if not mock_itsm:
                client = ServiceNowClient("https://dev-instance.service-now.com", token="fake")
                client.create_license_revocation_ticket(raw["assigned_user_email"], "Adobe Creative Cloud", raw["idle_days_license"])
            else:
                print(f"  [MOCK] Chamado automático de revogação gerado para {raw['assigned_user_email']}.")

    print("\n" + "=" * 60)
    print("PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    run_sync_pipeline(mock_itsm=True)
