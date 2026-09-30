from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class RawDeviceAsset(BaseModel):
    """
    Representa o ativo bruto extraído de soluções como Microsoft Intune, SCCM ou Jamf.
    """
    device_id: str = Field(description="ID do dispositivo no agente de inventário")
    serial_number: str = Field(description="Número de série físico da máquina")
    hostname: str = Field(description="Nome do host de rede")
    manufacturer: str = Field(description="Fabricante bruto informado pelo agente")
    model: str = Field(description="Modelo do hardware")
    os_name: str = Field(description="Sistema operacional")
    os_version: str = Field(description="Versão da build do SO")
    assigned_user_email: Optional[str] = Field(default=None, description="E-mail do usuário atribuído")
    last_checkin: datetime = Field(description="Último contato registrado pelo agente")
    idle_days_license: int = Field(default=0, description="Dias sem utilização de software licenciado (SAM)")

    @field_validator("serial_number")
    @classmethod
    def clean_serial(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned or cleaned in ["UNKNOWN", "DEFAULT", "NONE"]:
            raise ValueError(f"Serial number inválido: '{v}'")
        return cleaned

    @field_validator("hostname")
    @classmethod
    def clean_hostname(cls, v: str) -> str:
        return v.strip().lower()


class CMDBConfigurationItem(BaseModel):
    """
    Representa o Configuration Item (CI) normalizado pronto para a Table API / IRE do ITSM (ServiceNow / BMC).
    """
    serial_number: str
    name: str = Field(description="Nome do CI no CMDB")
    manufacturer: str
    model_id: str
    os: str
    os_version: str
    assigned_to: Optional[str] = None
    install_status: str = Field(default="In Use", description="Status do CI no ciclo de vida")
    operational_status: str = Field(default="Operational")
    u_last_inventory_sync: str = Field(description="Timestamp formatado da sincronização")
    comments: Optional[str] = None
