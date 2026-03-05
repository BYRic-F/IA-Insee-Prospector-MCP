import csv
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

logger = logging.getLogger("datagouv_mcp")

def register_fetch_sirene_data_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    async def fetch_sirene_data(
        q: str,
        filename: str = "sirene_export.csv",
    ) -> str:
        """
        Fetch data from Insee Sirene API v3.11 and export to CSV.
        
        Args:
            q: Solr query string (e.g. "codeCommuneEtablissement:44109 AND periode(activitePrincipaleEtablissement:10.71C AND etatAdministratifEtablissement:A)")
            filename: Name of the output CSV file in the exports directory.
        """
        api_key = os.getenv("DATAGOUV_API_KEY")
        if not api_key:
            return "Error: DATAGOUV_API_KEY environment variable is not set."

        base_url = "https://api.insee.fr/api-sirene/3.11/siret"
        headers = {
            "X-INSEE-Api-Key-Integration": api_key,
            "Accept": "application/json",
        }
        params = {
            "q": q,
            "nombre": 100,
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching Sirene data with query: {q}")
                resp = await client.get(base_url, headers=headers, params=params, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                return f"Error: HTTP {e.response.status_code} - {e.response.text}"
            except Exception as e:
                return f"Error: {str(e)}"

        etablissements = data.get("etablissements", [])
        if not etablissements:
            return "No results found for this query."

        # Ensure exports directory exists
        os.makedirs("./exports", exist_ok=True)
        filepath = os.path.join("./exports", filename)

        results = []
        for etab in etablissements:
            unite = etab.get("uniteLegale", {})
            periodes = etab.get("periodesEtablissement", [{}])
            periode0 = periodes[0] if periodes else {}
            adresse = etab.get("adresseEtablissement", {})

            # Mapping logic from gemini.md
            # Nom
            nom = unite.get("denominationUniteLegale")
            if not nom:
                nom = f"{unite.get('nomUniteLegale', '')} {unite.get('prenom1UniteLegale', '')}".strip()
            if not nom:
                nom = periode0.get("enseigne1Etablissement")
            
            # NAF
            naf = periode0.get("activitePrincipaleEtablissement")
            if not naf:
                naf = unite.get("activitePrincipaleUniteLegale")
            
            # Effectifs
            effectifs = etab.get("trancheEffectifsEtablissement")
            
            # Adresse
            addr_parts = [
                adresse.get("numeroVoieEtablissement"),
                adresse.get("typeVoieEtablissement"),
                adresse.get("libelleVoieEtablissement"),
                adresse.get("codePostalEtablissement"),
                adresse.get("libelleCommuneEtablissement")
            ]
            full_address = " ".join([str(p) for p in addr_parts if p]).strip()

            results.append({
                "Siret": etab.get("siret"),
                "Nom": nom or "Inconnu",
                "Code NAF": naf or "Inconnu",
                "Tranche Effectifs": effectifs or "Inconnu",
                "Adresse": full_address or "Inconnu"
            })

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Siret", "Nom", "Code NAF", "Tranche Effectifs", "Adresse"])
                writer.writeheader()
                writer.writerows(results)
            return f"Successfully exported {len(results)} establishments to {filepath}"
        except Exception as e:
            return f"Error writing CSV: {str(e)}"
