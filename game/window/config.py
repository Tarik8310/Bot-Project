import tkinter as tk
from tkinter import messagebox

class Configuration(tk.Frame):
    """
    Étape 2 : Configuration des Paramètres de la Partie.

    Permet à l'utilisateur de définir les règles de la partie
    via des curseurs :
    - Énergie initiale des robots (500 à 3000).
    - Distance de repérage (vision des robots, 2 à 6 cases).
    - Nombre de robots participants (2 à 6).
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller

        # Styles
        label_font = ("Helvetica", 14)
        title_font = ("Helvetica", 28, "bold")

        # Titre
        tk.Label(
            self, 
            text="Étape 2 : Paramètres de la Partie", 
            font=title_font, fg="white", bg="#1e1e1e"
        ).pack(pady=30)

        frame_reglages = tk.Frame(self, bg="#1e1e1e")
        frame_reglages.pack(fill="x", padx=100, pady=20)

        # Slider 1: Énergie 
        self.scale_energie = tk.Scale(
            frame_reglages, from_=500, to=3000, orient="horizontal",
            label="Énergie initiale des robots", length=500, 
            bg="#1e1e1e", fg="white", font=label_font, troughcolor="#505050",
            highlightthickness=0
        )
        self.scale_energie.set(1500)
        self.scale_energie.pack(pady=20)

        # Slider 2: Distance de Repérage
        self.scale_distance = tk.Scale(
            frame_reglages, from_=2, to=6, orient="horizontal",
            label="Distance de repérage (Vision)", length=500, 
            bg="#1e1e1e", fg="white", font=label_font, troughcolor="#505050",
            highlightthickness=0
        )
        self.scale_distance.set(4)
        self.scale_distance.pack(pady=20)

        # Slider 3: Nombre de Robots
        self.scale_nb_robots = tk.Scale(
            frame_reglages, from_=2, to=6, orient="horizontal",
            label="Nombre de robots participants", length=500, 
            bg="#1e1e1e", fg="white", font=label_font, troughcolor="#505050",
            highlightthickness=0
        )
        self.scale_nb_robots.set(2)
        self.scale_nb_robots.pack(pady=20)

        # Navigation
        frame_nav = tk.Frame(self, bg="#1e1e1e")
        frame_nav.pack(side="bottom", fill="x", padx=50, pady=40)

        # Bouton Retour 
        tk.Button(
            frame_nav, text="← Retour", font=("Helvetica", 14, "bold"),
            fg="white", bg="#3a3a3a", width=15,
            command=self.on_return
        ).pack(side="left")

        # Bouton Suivant 
        tk.Button(
            frame_nav, text="Suivant →", font=("Helvetica", 14, "bold"),
            fg="white", bg="#006400", width=15,
            command=self.aller_suivant
        ).pack(side="right")

    def aller_suivant(self):
        """
        Valide les choix, sauvegarde les paramètres dans le contrôleur et passe à l'étape suivante.
        
        Récupère les valeurs actuelles des sliders :
        - energie
        - distance
        - nb_robots
        Et les stocke dans `self.controller.parametres_partie`.
        Ensuite, navigue vers l'écran "Selection".
        """
        
        # On enregistre les choix dans le contrôleur
        self.controller.parametres_partie["energie"] = self.scale_energie.get()
        self.controller.parametres_partie["distance"] = self.scale_distance.get()
        self.controller.parametres_partie["nb_robots"] = self.scale_nb_robots.get()
        
        print(f"Paramètres validés : {self.controller.parametres_partie}")
        
        # On passe à la nouvelle page
        self.controller.show_frame("Selection") # Assurez-vous que la classe s'appelle bien Selection ou RobotSelection dans main.py
        
    def on_return(self):
        """
        Retourne à l'étape précédente (Configuration de la carte).
        """
        #Retour au menu principal
        self.controller.show_frame("Mapconfig")