import pandas as pd
from typing import List, Dict, Any
from src.schemas import CMDBConfigurationItem

MANUFACTURER_MAP = {
    "DELL INC.": "Dell",
    "DELL": "Dell",
    "LENOVO": "Lenovo",
    "APPLE": "Apple",
    "APPLE INC.": "Apple",
    "HEWLETT-PACKARD": "HP",
    "HP": "HP"
}

def normalize_manufacturer(name: str) -> str:
    cleaned = str(name).strip().upper()
    return MANUFACTURER_MAP.get(cleaned, str(name).strip().title())

def reconcile_and_normalize(assets_raw: List[Dict[str, Any]]) -> List[CMDBConfigurationItem]:
    """
    Executa a reconciliação e normalização de dados com Pandas:
    1. Higieniza nomes e fabricantes;
    2. Deduplica registros baseando-se no serial_number (chave física do hardware);
    3. Prioriza o registro com o last_checkin mais recente;
    4. Converte para o schema de CI do CMDB.
    """
    if not assets_raw:
        return []

    df = pd.DataFrame(assets_raw)

    # 1. Padronização preliminar
    df["serial_number"] = df["serial_number"].astype(str).str.strip().str.upper()
    df["hostname"] = df["hostname"].astype(str).str.strip().str.lower()
    df["manufacturer"] = df["manufacturer"].apply(normalize_manufacturer)
    df["last_checkin"] = pd.to_datetime(df["last_checkin"])

    # 2. Reconciliação / Deduplicação: Ordena por last_checkin decrescente e remove duplicados de serial_number
    df_sorted = df.sort_values(by="last_checkin", ascending=False)
    df_dedup = df_sorted.drop_duplicates(subset=["serial_number"], keep="first")

    normalized_cis: List[CMDBConfigurationItem] = []

    for _, row in df_dedup.iterrows():
        # Ciclo de vida: se máquina não faz check-in há mais de 90 dias, marca status diferente
        days_inactive = (pd.Timestamp.now(tz=row["last_checkin"].tz) - row["last_checkin"]).days if row["last_checkin"].tz else (pd.Timestamp.now() - row["last_checkin"]).days
        status = "Retired" if days_inactive > 90 else "In Use"

        ci = CMDBConfigurationItem(
            serial_number=row["serial_number"],
            name=row["hostname"],
            manufacturer=row["manufacturer"],
            model_id=str(row.get("model", "Generic Computer")),
            os=str(row.get("os_name", "Unknown")),
            os_version=str(row.get("os_version", "")),
            assigned_to=row.get("assigned_user_email"),
            install_status=status,
            operational_status="Non-Operational" if status == "Retired" else "Operational",
            u_last_inventory_sync=row["last_checkin"].isoformat(),
            comments=f"Reconciliado via pipeline ITAM-ITSM. Inativo por {days_inactive} dias."
        )
        normalized_cis.append(ci)

    return normalized_cis
