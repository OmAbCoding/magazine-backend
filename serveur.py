from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import stripe

app = FastAPI()
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # L'étoile veut dire "Tout le monde est autorisé"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connexion = sqlite3.connect("magazine.db", check_same_thread=False)
curseur = connexion.cursor()

curseur.execute("""
          CREATE TABLE IF NOT EXISTS abonnes (
          email TEXTE UNIQUE,
          duree_mois INTEGER)
""")
connexion.commit()


@app.get("/")
def accueil():
    return {"message" : "Teste de mise à jour en direct ! "}

@app.get("/abonnement/{nom_client}")

def verifier_abonnement(nom_client: str):
    if nom_client.lower() == "eric":
        return {
            "client": nom_client,
            "statut": "Actif",
            "acces_premium": True
        }
    else:
        return {
            "client": nom_client,
            "statut": "Inactif",
            "acces_premium": False
        }

class NouvelAbonne(BaseModel):
    email: str
    duree_mois: int

@app.post("/inscription")
def inscrire_client(donnees: NouvelAbonne):
    try:
        curseur.execute(
            "INSERT INTO abonnes (email, duree_mois) VALUES (?,?)", (donnees.email, donnees.duree_mois)
        )
        connexion.commit()

        return {"message": f"Succès ! {donnees.email} est définitivement sauvegardé en base de données.",
                "facture": donnees.duree_mois * 10}

    except sqlite3.IntegrityError:
        return {"erreur":f"Attention! l'email {donnees.email} est déja abonné au magazine"}

@app.get("/admin/abonnes")
def voir_tous_les_abonnes(mot_de_passe: str = ""):
    if mot_de_passe != "Artiste2026":
        return {"alerte": "Accès refusé"}
    
    curseur.execute("SELECT * FROM abonnes")
    tous_les_clients = curseur.fetchall()
    return {"nombre_total": len(tous_les_clients), "clients": tous_les_clients}

@app.post("/creer-paiement")
def creer_paiement():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data" : {
                        "name" : "Abonnement 1 an - Artistes Magazine",
                    },
                    "unit_amount" : 12000,
                },
                "quantity" : 1,
            }],
            mode="payment",
            success_url="http://127.0.0.1:8000/docs",
            cancel_url="http://127.0.0.1:8000/docs",
        )

        return{"url_paiement" : session.url}

    except Exception as e : 
        return {"erreur" : str(e)}