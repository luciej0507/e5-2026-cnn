import json

import streamlit as st
import requests
from metrics_utils import lire_metrics, somme, par_label, moyenne_ms

# Configuration des URLs de l'API
from config import API_UPLOAD_URL, API_PREDICTIONS_URL

# Titre de l'application
st.title("🛰️ Application CNN - Classification d'Images Satellites")

# Ajout de la **sidebar** pour la navigation
st.sidebar.title("🔍 Navigation")
menu = st.sidebar.radio("Navigation", ["📤 Upload d'image", "📋 Voir les prédictions", "📊 Dashboard"])

# Télécharger les prédictions indépendamment de la page affichée.
try:
    pourfichier = requests.post(API_PREDICTIONS_URL, timeout=(5, 30))
    pourfichier.raise_for_status()
    predictionsjson = pourfichier.json()
    st.sidebar.download_button(
        label="Télécharger le JSON",
        data=json.dumps(predictionsjson, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="predictions.json",
        mime="application/json",
    )
except requests.exceptions.RequestException as e:
    st.sidebar.error(f"Erreur lors du chargement du JSON : {e}")

# Page : Upload d'image
if menu == "📤 Upload d'image":
    st.header("📤 Upload d'une image et envoi vers l'API")

    # Formulaire de dépôt de fichier
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Choisissez une image", type=["jpg", "jpeg", "png"])
        submit_button = st.form_submit_button("Envoyer")

    # Si le formulaire est soumis
    if submit_button:
        if uploaded_file is not None:
            # Afficher l'image uploadée
            st.image(uploaded_file, caption="Image envoyée", use_container_width=True)

            # Préparer le fichier pour l'envoi à l'API
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

            # Envoie la requête POST à l'API
            try:
                response = requests.post(API_UPLOAD_URL, files=files, timeout=(5, 120))
                response.raise_for_status()  # Vérifie si l'API retourne une erreur HTTP

                # Affiche la réponse de l'API
                st.success("✅ Réponse de l'API :")
                st.json(response.json())

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erreur lors de la communication avec l'API : {e}")
        else:
            st.warning("⚠️ Veuillez sélectionner une image avant d'envoyer.")

# Page : Voir les prédictions enregistrées
elif menu == "📋 Voir les prédictions":
    st.header("📋 Liste des prédictions enregistrées")

    # Récupérer les prédictions depuis l'API
    try:
        response = requests.get(API_PREDICTIONS_URL, timeout=(5, 30))
        response.raise_for_status()
        predictions = response.json()

        # Vérifier s'il y a des prédictions
        if predictions:
            for prediction in predictions:
                with st.expander(f"📌 Prédiction {prediction['id']}"):
                    st.write(prediction["image"])
                    st.write(f"🔹 **Label prédit** : {prediction['label']}")
                    st.write(f"📝 **Commentaire** : {prediction['commentaire']}")
                    st.write(f"🛠️ **Modèle utilisé** : {prediction['modele']}")
        else:
            st.info("Aucune prédiction enregistrée pour le moment.")
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors de la récupération des prédictions : {e}")

# Page : Dashboard de monitoring
elif menu == "📊 Dashboard":
    st.header("📊 Dashboard de monitoring")
    st.button("🔄 Rafraîchir")

    try:
        samples = lire_metrics()

        # --- Modèle CNN ---
        st.subheader("Modèle CNN")
        col1, col2 = st.columns(2)
        col1.metric("Prédictions totales", int(somme(samples, "predictions_total")))
        inference = moyenne_ms(samples, "prediction_duration_seconds")
        col2.metric(
            "Durée moyenne d'inférence",
            "—" if inference is None else f"{inference:.0f} ms",
        )

        classes = par_label(samples, "predictions_total", "label")
        total_pred = sum(classes.values())
        if classes:
            st.caption("Répartition des classes prédites")
            colonnes = st.columns(len(classes))
            for col, (nom, n) in zip(colonnes, sorted(classes.items())):
                col.metric(nom, f"{int(n)} ({n / total_pred:.0%})")
        else:
            st.info("Aucune prédiction depuis le démarrage de l'API.")

        # --- Bug ticket 4 ---
        st.subheader("Ticket 4 : cohérence de la liste")
        incoherences = int(somme(samples, "liste_predictions_incoherences_total"))
        if incoherences == 0:
            st.success("Aucune incohérence détectée.")
        else:
            st.error(f"{incoherences} incohérence(s) détectée(s) !")

        # --- API ---
        st.subheader("API")
        statuts = par_label(samples, "http_requests_total", "status")

        if statuts:
            st.metric("Requêtes totales", int(sum(statuts.values())))

            colonnes = st.columns(min(len(statuts), 4))
            for i, (code, n) in enumerate(sorted(statuts.items())):
                icone = "✅" if code.startswith("2") else "⚠️" if code.startswith("4") else "🔥"
                colonnes[i % len(colonnes)].metric(f"{icone} {code}", int(n))

            erreurs_serveur = sum(n for c, n in statuts.items() if c.startswith("5"))
            if erreurs_serveur == 0:
                st.success("Aucune erreur serveur depuis le démarrage de l'API.")
            else:
                st.error(f"{int(erreurs_serveur)} erreur(s) serveur depuis le démarrage.")
        else:
            st.info("Aucune requête enregistrée.")

        # --- Base de données ---
        st.subheader("Base de données")
        col3, col4 = st.columns(2)
        col3.metric("Erreurs BDD", int(somme(samples, "db_errors_total")))
        duree_bdd = moyenne_ms(samples, "db_query_duration_seconds")
        col4.metric(
            "Durée moyenne des requêtes",
            "—" if duree_bdd is None else f"{duree_bdd:.0f} ms",
        )

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Impossible de lire les métriques de l'API : {e}")