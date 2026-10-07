from app.bdd.connexion import Connexion
from app.bdd.prediction import Prediction
from app.metrics import mesurer_bdd, LISTING_MISMATCH
import logging

logger = logging.getLogger(__name__)


class Service_Prediction(Connexion):
    @classmethod
    def sauvegarder_prediction(cls, prediction: Prediction):
        with cls.ouvrir_connexion() as (bdd, cursor):
            cursor.execute("SELECT id FROM labels")
            labels = cursor.fetchall()

            if labels is None:
                raise ValueError(f"Label absent de la base : {prediction.label}")
            
            cursor.execute(
                "INSERT INTO predictions (image, label, commentaire, modele) VALUES (%s, %s, %s, %s)",
                [prediction.image, labels[0]["id"], prediction.commentaire, prediction.modele],
            )

            bdd.commit()
            prediction.id = cursor.lastrowid
        return prediction

    @classmethod
    @mesurer_bdd("lister_predictions")
    def lister_predictions(cls):
        with cls.ouvrir_connexion() as (_, cursor):
            cursor.execute(
                "SELECT predictions.image as image, labels.label as label, predictions.commentaire as commentaire, predictions.modele as modele FROM predictions JOIN labels ON predictions.label = labels.id"
            )
            rows = cursor.fetchall()  
                      
            resultat = [Prediction(**row) for row in rows]  # bug du ticket4 corrigé
           
            if len(resultat) != len(rows):
                LISTING_MISMATCH.inc()
                logger.error(
                    "Incohérence liste prédictions : %d lues en base, %d renvoyées",
                    len(rows), len(resultat),
                )
            else:
                logger.info("Liste des prédictions OK : %d renvoyée(s)", len(resultat))
            return resultat
