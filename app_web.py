import streamlit as st
import pandas as pd
import os
import glob
import time
from google import genai
from google.genai import types

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Prospection Insee", layout="wide", page_icon="🚀")
st.title("🚀 Agent de Prospection Insee")
st.markdown("Interrogez la base Sirene en langage naturel via Gemini 3.1 & MCP.")

# --- INITIALISATION ---
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Dossier de stockage des résultats
EXPORT_DIR = "exports"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    # Utilisation du modèle 3.1 validé
    model_name = st.selectbox("Sélectionner le modèle", [
        "gemini-3.1-flash-lite-preview",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp"
    ])
    st.info("L'IA génère un fichier CSV automatisé via l'API Sirene et le serveur MCP.")

# --- ZONE DE SAISIE ---
prompt = st.text_area(
    "Que recherchez-vous ?", 
    placeholder="Ex: PME informatique à Lyon, plus de 20 salariés...",
    help="Précisez la ville, le secteur (NAF) et l'effectif."
)

# --- MOTEUR DE RECHERCHE ---
if st.button("Lancer l'extraction", type="primary"):
    if not prompt:
        st.error("Veuillez saisir une demande de prospection.")
    else:
        with st.spinner("L'IA exécute le protocole Insee (MCP + Code Execution)..."):
            try:
                # Tes instructions de prospection Insee
                sys_inst = (
                    "Tu es en mode Prospection Insee activé. Tu dois impérativement :\n"
                    "1. Passer par le serveur MCP pour exécuter un script Python.\n"
                    "2. Utiliser la clé DATAGOUV_API_KEY via le header X-INSEE-Api-Key-Integration.\n"
                    "3. Interroger l'API Sirene v3.11 sur l'endpoint /siret.\n"
                    "4. Appliquer les filtres demandés (Ville, Code NAF, Effectif).\n"
                    "5. Exporter les résultats dans un fichier CSV structuré dans 'exports/'.\n"
                    "6. Supprimer systématiquement tes scripts de travail (.py) après l'extraction."
                )

                # Appel à Gemini avec gestion du dictionnaire config
                response = client.models.generate_content(
                    model=model_name,
                    config={
                        "system_instruction": sys_inst,
                        "tools": [{"code_execution": {}}] 
                    },
                    contents=f"Demande client : {prompt}"
                )
                
                
                print("--- DEBUG DES ENTRAILLES ---")
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'executable_code') and part.executable_code:
                        print(f"CODE GÉNÉRÉ PAR L'IA :\n{part.executable_code.code}")
                    if hasattr(part, 'code_execution_result') and part.code_execution_result:
                        print(f"RÉSULTAT DE L'EXÉCUTION :\n{part.code_execution_result.output}")
                print("-----------------------------")
                # ------------------------------------

                st.success("Extraction terminée avec succès !")
                time.sleep(2) 
                st.rerun()
                
                # Gestion propre de la réponse (évite l'erreur non-text parts)
                full_text = ""
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            full_text += part.text
                
                if full_text:
                    print(f"DEBUG IA: {full_text[:100]}...")
                
                st.success("Extraction terminée avec succès !")
                time.sleep(2) # Pause pour l'écriture disque
                st.rerun()

            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")

st.divider()

# --- VISUALISATION DES RÉSULTATS ---
st.subheader("📊 Derniers fichiers générés")

# Récupération des fichiers CSV
list_of_files = glob.glob(f'{EXPORT_DIR}/*.csv')

if list_of_files:
    # On prend le plus récent
    latest_file = max(list_of_files, key=os.path.getctime)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"📄 **Fichier :** `{os.path.basename(latest_file)}`")
        try:
            df = pd.read_csv(latest_file)
            st.dataframe(df, use_container_width=True, height=400)
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

    with col2:
        st.markdown("### 📥 Actions")
        with open(latest_file, "rb") as f:
            st.download_button(
                label="Télécharger le CSV",
                data=f,
                file_name=os.path.basename(latest_file),
                mime="text/csv",
            )
        
        # Petit graphique bonus
        if 'trancheEffectifsEtablissement' in df.columns:
            st.write("---")
            st.write("**Répartition des effectifs :**")
            st.bar_chart(df['trancheEffectifsEtablissement'].value_counts())
else:
    st.info("Aucune donnée disponible. Lancez votre première recherche ci-dessus.")