"""
Fichier principal de l'application Robots Wars.

Ce script sert de point d'entrée (entry point) pour l'application.
Il initialise la fenêtre principale Tkinter, configure les paramètres globaux,
"""
# Importation des ressources Tkinter
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

# --- Importation des Écrans ---
from window.main_menu import Menu
from window.localoronline import Mode
from window.map_config import Mapconfig
from window.config import Configuration
from window.select import Selection
from window.gameplay import Gameplay
from window.online_lobby import OnlineLobby
from window.online_gameplay import OnlineGameplay

# ======================
#      CLASSE APP
# ======================

class App(tk.Tk):
    """
    Classe principale héritant de tk.Tk (la fenêtre racine).

    Attributs:
        parametres_partie (dict): Un dictionnaire centralisé pour stocker les données
                                  de la partie en cours de configuration (ex: la carte,
                                  la liste des robots, l'énergie, la vitesse, etc.).
                                  Cela permet aux différentes fenêtres de communiquer.
        frames (dict): Un dictionnaire stockant les instances de chaque écran,
                       avec pour clé le nom de la classe (ex: "Menu", "Gameplay").
    """

    def __init__(self):
        """
        Constructeur de l'application. Initialise la fenêtre et charge les écrans.
        """
        super().__init__()

        # --- Configuration de la Fenêtre Principale ---
        self.title("Robots Wars")
        self.geometry("1600x900")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")  
        
        # Initialisation du stockage des données partagées
        # Le dictionnaire sera rempli progressivement par les écrans de configuration
        self.parametres_partie = {}  

        # --- Création du Conteneur Principal ---
        # C'est une Frame qui remplit toute la fenêtre et qui contiendra
        # toutes les fenetres de l'application superposées.
        container = tk.Frame(self, bg="#1e1e1e")
        container.pack(fill="both", expand=True)
        
        # Configuration de la grille : le conteneur a une seule cellule (0,0)
        # qui prend toute la place et où toutes les frames seront empilées.
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- Initialisation des Écrans ---
        self.frames = {}

        # Liste de toutes les classes d'écran 
        les_ecrans = (
            Menu, 
            Mode, 
            Mapconfig, 
            Configuration, 
            Selection, 
            Gameplay, 
            OnlineLobby, 
            OnlineGameplay
        )

        for F in les_ecrans:
            # On instancie chaque écran en lui passant :
            # - parent : le conteneur (pour l'affichage)
            # - controller : 'self' (pour qu'ils puissent appeler show_frame et accéder à parametres_partie)
            frame = F(parent=container, controller=self)
            
            # On stocke l'instance dans le dictionnaire avec le nom de la classe comme clé
            self.frames[F.__name__] = frame
            
            # On place la frame dans la grille. 
            frame.grid(row=0, column=0, sticky="nsew")

        # --- Lancement ---
        # On affiche le menu principal au démarrage
        self.show_frame("Menu")

    def show_frame(self, name):
        """
        Affiche l'écran correspondant au nom de classe donné.

        Cette méthode fait passer la frame demandée au premier plan

        Args:
            name (str): Le nom exact de la classe de la frame à afficher 
                        (ex: "Menu", "Gameplay", "Mapconfig").
        """
        print(f"Navigation vers: {name}")
        
        # Récupération de l'instance de la frame
        frame = self.frames[name]
        
        # La méthode tkraise() place le widget au-dessus des autres dans la pile d'affichage
        frame.tkraise()

# ======================
#         MAIN
# ======================

if __name__ == "__main__":
    # Création de l'instance de l'application
    app = App()
    
    # Démarrage de la boucle principale de Tkinter
    app.mainloop()