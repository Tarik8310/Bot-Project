import tkinter as tk
from tkinter import messagebox

# ======================
#      MENU PRINCIPAL
# ======================

class Menu(tk.Frame):
    """Fenêtre d'accueil du jeu"""
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller

        # Titre principal 
        titre = tk.Label(
            self,
            text="Robots Wars",
            font=("Helvetica", 36, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        titre.pack(pady=100)

        # Style des boutons
        btn_font = ("Helvetica", 18, "bold")
        btn_fg = "white"
        btn_bg = "#3a3a3a"
        btn_active = "#505050"

        # Boutons du menu principal
        # J'ai renommé "Paramètres" en "Raccourcis" pour être plus clair
        boutons = [
            ("Jouer", self.on_play),
            ("Aide", self.on_help),
            ("Raccourcis", self.on_settings),
            ("Quitter", controller.destroy)
        ]

        for texte, action in boutons:
            b = tk.Button(
                self,
                text=texte,
                font=btn_font,
                fg=btn_fg,
                bg=btn_bg,
                activebackground=btn_active,
                activeforeground="white",
                width=20,
                command=action
            )
            b.pack(pady=10)

    def on_play(self):
        """Passe à la fenêtre du choix du mode de jeu"""
        self.controller.show_frame("Mode")

    def on_help(self):
        messagebox.showinfo(
            "Aide",
            "Bienvenue dans La Guerre des Robots !\n\n"
            "Dans ce jeu, vous faites combattre des robots sur un terrain rempli d'obstacle et de mines.\n"
            "1. Commencez par configurer le terrain et les obstacles.\n"
            "2. Configurez les paramètres de la partie (nombre de robots, energie de départ, distance de repérage).\n"
            "3. Sélectionnez les fichiers de vos robots (.rbt) à utiliser.\n"
            "Cliquez sur 'Jouer' pour commencer une partie.\n"
            "GOOD LUCK AND HAVE FUN!"
        )

    def on_settings(self):
        """Ouvre une fenêtre popup affichant les raccourcis clavier"""
        
        # Création d'une fenêtre secondaire (Popup)
        settings_window = tk.Toplevel(self)
        settings_window.title("Raccourcis")
        settings_window.geometry("500x350") # Un peu plus large pour le texte
        settings_window.configure(bg="#1e1e1e")
        settings_window.resizable(False, False)

        # Titre de la popup
        tk.Label(
            settings_window, 
            text="Raccourcis Clavier", 
            font=("Helvetica", 20, "bold"), 
            fg="white", bg="#1e1e1e"
        ).pack(pady=30)

        # Conteneur pour la liste
        info_frame = tk.Frame(settings_window, bg="#1e1e1e")
        info_frame.pack(pady=10)

        # Liste des raccourcis à afficher
        shortcuts = [
            ("Touche 'P'", "Mettre en Pause / Reprendre"),
            ("Barre Espace", "Modifier la vitesse du jeu"),
            ("Echap", "Quitter la partie en cours"),
        ]

        for key, description in shortcuts:
            row = tk.Frame(info_frame, bg="#1e1e1e")
            row.pack(fill="x", pady=10)
            
            # La touche (en vert pour ressortir)
            tk.Label(
                row, 
                text=key, 
                font=("Helvetica", 14, "bold"), 
                fg="#00FF00", 
                bg="#1e1e1e",
                width=15, anchor="e"
            ).pack(side="left", padx=10)

            # Séparateur
            tk.Label(
                row, text=":", font=("Helvetica", 14, "bold"), 
                fg="white", bg="#1e1e1e"
            ).pack(side="left")

            # La description
            tk.Label(
                row, 
                text=description, 
                font=("Helvetica", 12), 
                fg="white", 
                bg="#1e1e1e",
                anchor="w"
            ).pack(side="left", padx=10)

        # Bouton Fermer
        tk.Button(
            settings_window,
            text="Fermer",
            font=("Helvetica", 12),
            bg="#3a3a3a", fg="white",
            command=settings_window.destroy
        ).pack(side="bottom", pady=20)