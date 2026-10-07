# Ticket d'incident 4

## Étapes pour reproduire le problème
1. A la première utilisation, lorsqu'il n'y a aucune prédiction.
2. Lancer l'application.
3. Ajouter une image satellite du désert sur la page *Upload image*.
4. *Envoyer*
6. Passer sur la page *Voir les prédictions*.
7. La *Liste des prédictions enregistrées* est vide.

## Résultat actuel
Malgré l'ajout d'une première prédiction, la *Liste des prédictions enregistrées* affiche *Aucune prédiction enregistrée pour le moment.*.

![Capture d'écran de l'incident](./ressources/ticket4.png)

## Comportement attendu
La *Liste des prédictions enregistrées* doit afficher la première *prédiction*.

---

# Correction

**Date de la correction : 7 octobre 2026**

### Cause du bug
Dans `api/app/bdd/service.py`, la méthode `lister_predictions` retirait systématiquement la dernière ligne renvoyée par la base de données (table *predictions*)  :

``` python
length = len(rows)-1
return [Prediction(**row) for row in rows[:length]]
```

Avec une seule prédiction, `length` valait 0 et la liste renvoyée était vide. Avec N prédictions, seules N-1 étaient affichées : le bug touchait donc toutes les prédictions, pas uniquement la première.

### Correction apportée
La liste est maintenant construite à partir de toutes les lignes :

``` python
return [Prediction(**row) for row in rows]
```

### Autres modifications
- **Tests unitaires** (`api/tests/`, `pytest`) : tests de non-régression avec une base simulée (`unittest.mock`). Avec le bug, 4 tests échouent ; avec la correction, les 6 passent.
- **Contrôle dans le code** : `lister_predictions` écrit un log (`Liste des prédictions OK : N renvoyée(s)`, ou une erreur en cas d'incohérence) et incrémente le compteur `liste_predictions_incoherences_total` si le nombre de lignes renvoyées diffère du nombre de lignes lues.
- **Monitoring** (Prometheus + Grafana, dossier `monitoring/`) : l'API expose `/metrics` (prédictions par classe, durée d'inférence du modèle, requêtes HTTP par code, durée et erreurs de la base, compteur d'incohérences du ticket 4). 
- **Dashboard Streamlit** : nouvelle page *📊 Dashboard* dans la sidebar, qui lit `/metrics`.

### Résumé des fichiers créés ou modifiés

| Fichier | Modification |
|---|---|
| `api/app/bdd/service.py` | **Correction du bug** (`rows[:length]` devient `rows`), logs et compteur d'incohérences |
| `api/app/main.py` | Exposition de `/metrics`, métriques d'inférence du modèle CNN, configuration des logs |
| `api/app/metrics.py` | *Nouveau* : définition des métriques Prometheus et décorateur `mesurer_bdd` |
| `api/tests/` | *Nouveau* : tests unitaires (`test_service.py`, `conftest.py`) |
| `api/pytest.ini` | *Nouveau* : configuration de pytest |
| `api/requirements.txt` | Ajout de `prometheus-client` et `prometheus-fastapi-instrumentator` |
| `client/app.py` | nouvelle page *Dashboard* |
| `client/metrics_utils.py` | *Nouveau* : lecture et calcul des métriques pour le dashboard |
| `client/config.py` | Ajout de `API_METRICS_URL` |
| `client/Dockerfile` | Copie de `metrics_utils.py` |
| `client/requirements.txt` | Ajout de `prometheus-client` |
| `docker-compose.yml` | Ajout des services `prometheus` et `grafana` |
| `monitoring/` | *Nouveau* : `prometheus.yml` (configuration de la collecte des métriques) et `grafana/datasource.yml` (source de données Prometheus configurée automatiquement dans Grafana) |