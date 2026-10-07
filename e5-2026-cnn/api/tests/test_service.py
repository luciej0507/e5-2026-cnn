from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.bdd.service import Service_Prediction
from app.bdd.prediction import Prediction


# Préparation des tests
# l'accès à la base est simulé, la logique testée est celle de ton code
def fausse_connexion(rows):
    """Remplace ouvrir_connexion() : renvoie un curseur qui retourne `rows`."""
    cursor = MagicMock()
    cursor.fetchall.return_value = rows

    @contextmanager
    def _ouvrir_connexion():
        yield MagicMock(), cursor

    return _ouvrir_connexion, cursor


def ligne(image="desert_1.png", label="desert", commentaire="ok", modele="cnn_v1"):
    return {"image": image, "label": label, "commentaire": commentaire, "modele": modele}


def lister_avec(rows):
    ouvrir, cursor = fausse_connexion(rows)
    with patch.object(Service_Prediction, "ouvrir_connexion", staticmethod(ouvrir)):
        return Service_Prediction.lister_predictions(), cursor


# --- Test de non-régression du ticket #4 ---
# Reproduction du bug
def test_une_seule_prediction_est_retournee():
    """Bug du ticket : avec 1 seule ligne, la liste revenait vide (len - 1 = 0)."""
    resultat, _ = lister_avec([ligne()])

    assert len(resultat) == 1
    assert isinstance(resultat[0], Prediction)


# --- Cas limites ---
# protège le cas « vraiment aucune prédiction »
# la correction ne doit pas casser l'affichage du message "Aucune prédiction enregistrée"
def test_aucune_prediction_retourne_liste_vide():
    resultat, _ = lister_avec([])

    assert resultat == []

# Montre que le bug ne touchait pas que la première utilisation : 
# il perdait toujours la dernière ligne, même avec beaucoup de données
def test_toutes_les_predictions_sont_retournees():
    """L'ancien code perdait toujours la dernière ligne."""
    rows = [ligne(image=f"img_{i}.png") for i in range(5)]

    resultat, _ = lister_avec(rows)

    assert len(resultat) == 5

# Vérification que les images ressortent dans le même ordre.
# La correction ne doit ni perdre de ligne ni mélanger l'ordre renvoyé par la base.
def test_l_ordre_des_predictions_est_conserve():
    rows = [ligne(image="a.png"), ligne(image="b.png"), ligne(image="c.png")]

    resultat, _ = lister_avec(rows)

    assert [p.image for p in resultat] == ["a.png", "b.png", "c.png"]


# --- Contenu des données ---
def test_les_champs_sont_correctement_mappes():
    resultat, _ = lister_avec(
        [ligne(image="x.png", label="foret", commentaire="beau", modele="cnn_v2")]
    )

    p = resultat[0]
    assert p.image == "x.png"
    assert p.label == "foret"
    assert p.commentaire == "beau"
    assert p.modele == "cnn_v2"


# --- Requête SQL ---
def test_la_requete_joint_la_table_labels():
    _, cursor = lister_avec([])

    cursor.execute.assert_called_once()
    requete = cursor.execute.call_args[0][0]
    assert "JOIN labels" in requete