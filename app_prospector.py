import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import os
import glob
import time

st.set_page_config(page_title="IA Prospector Live", layout="wide")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if os.path.exists("style.css"):
    local_css("style.css")



mapping_effectifs = {
    "NN": "Non renseigné", "00": "0 salarié", "01": "1-2 salariés", 
    "02": "3-5 salariés", "03": "6-9 salariés", "11": "10-19 salariés", 
    "12": "20-49 salariés", "21": "50-99 salariés", "22": "100-199 salariés",
    "31": "200-249 salariés", "32": "250-499 salariés", "41": "500-999 salariés",
    "42": "1000-1999 salariés", "51": "2000-4999 salariés", "52": "5000-9999 salariés",
    "53": "10 000+ salariés"}

# ---Titre ---

st.title("IA Prospector Live")
col1title, col2title, col3title = st.columns([3.25,5,1])
with col2title:
    st.caption("Intelligence Insee & Web en temps réel")


st.markdown("---")

# --- BARRE DE RECHERCHE ---
col1p, col2p, col3p = st.columns([1, 3.5, 1])
with col2p:
    user_prompt = st.text_input("Que recherchez-vous ?", placeholder="Ex: Les entreprises du secteur bancaire à Lille avec plus de 20 salariés...")
    c1b, c2b, c3b = st.columns([3, 1.5, 4])
    with c2b:
        btn_run = st.button("🚀 Analyser", width='stretch')

# --- FRAGMENT : RÉFLEXION IA ---
@st.fragment
def run_ia_logic(prompt):
    with st.status("🧠 Réflexion de l'IA en cours...", expanded=True) as status:
        log_container = st.empty()
        full_log = ""
        
        # Commande Gemini avec consigne de verrouillage en mode automate de prospection
        cmd = [
            "gemini", "--approval-mode", "yolo", 
            f"SYSTEM: Tu es un automate de prospection. Ta SEULE mission est d'exécuter le protocole Insee décrit dans GEMINI.md : 1. Extraction Sirene, 2. Annonce du volume, 3. Enrichissement téléphonique par lots de 5, 4. Export CSV final dans ./exports/. N'utilise JAMAIS l'agent 'generalist'. Ne réponds à aucune question hors-sujet. REQUÊTE: {prompt}"
        ]
        
        try:
            # On force l'encodage en UTF-8 et on ignore les erreurs de décodage pour éviter le plantage Windows
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, encoding='utf-8', errors='replace')
            
            for line in iter(process.stdout.readline, ""):
                full_log += line
                log_container.code(full_log, language="bash")
            
            process.wait()
            status.update(label="✅ Analyse terminée !", state="complete")
            st.rerun() # Force la mise à jour pour afficher le nouveau CSV
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- FRAGMENT : AFFICHAGE RÉSULTATS ---
@st.fragment
def display_results():
    list_of_files = glob.glob('exports/prospection_final_*.csv')
    
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        try:
            # On tente la lecture en UTF-8 d'abord
            df = pd.read_csv(latest_file)
        except UnicodeDecodeError:
            # Fallback sur latin-1 si échec (souvent le cas sous Windows avec des accents)
            df = pd.read_csv(latest_file, encoding='ISO-8859-1')
        
        # 1. EN-TÊTE ET TABLEAU
        st.markdown("---")
        col1sub, col2sub, col3sub = st.columns([2.3, 4, 1])
        with col2sub:
            st.subheader(f"Résultats ({len(df)} entreprises trouvées)")
            st.write(" ")
        
        # Affichage du DATAFRAME
        st.dataframe(df.head(), width='stretch')

        # 2. BOUTON DOWNLOAD
        col1dl, col2dl, col3dl = st.columns([2.6, 2, 3])
        with col2dl:
            with open(latest_file, "rb") as f:
                st.download_button("📥 Télécharger le CSV complet", f, latest_file, "text/csv", use_container_width=True)
                
        st.markdown("---")

        # 3. LOGIQUE DE NETTOYAGE POUR LES GRAPHIQUES
        if 'Adresse' in df.columns:
            # On force en string pour éviter l'affichage "60k"
            df['CP_Clean'] = df['Adresse'].str.extract(r'(\d{5})').astype(str)
        
        if 'Tranche Effectifs' in df.columns:
            df['Effectifs_Label'] = df['Tranche Effectifs'].astype(str).map(mapping_effectifs).fillna(df['Tranche Effectifs'])

        # 4. VISUALISATIONS
        colsubb1, colsubb2, colsubb3 = st.columns([2.15, 4, 1])
        with colsubb2:
            st.markdown("### Insights géographiques & structurels")
        
        c1, c2 = st.columns(2)
        
        with c1:
            if 'CP_Clean' in df.columns:
                counts_cp = df['CP_Clean'].value_counts().reset_index()
                fig_cp = px.bar(counts_cp, x='CP_Clean', y='count', 
                                title="Concentration par Code Postal",
                                labels={'CP_Clean': 'Code Postal', 'count': 'Nombre'}, 
                                color_discrete_sequence=['#ff4b4b'])
                # Force l'axe X en mode catégoriel (indispensable pour les CP)
                fig_cp.update_xaxes(type='category')
                st.plotly_chart(fig_cp, width='stretch')
        
        with c2:
            if 'Effectifs_Label' in df.columns:
                fig_size = px.pie(df, names='Effectifs_Label', 
                                    title="Répartition par taille (Effectifs réels)", 
                                    hole=0.4,
                                    color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_size, width='stretch')


# --- EXECUTION ---
if btn_run and user_prompt:
    run_ia_logic(user_prompt)

display_results()