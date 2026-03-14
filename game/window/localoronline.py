import tkinter as tk
"""
Fichier définissant l'écran de choix entre le mode local et le mode en ligne.
Contient la classe Mode.
Permet de choisir entre:
- Le mode local (bouton "Mode Local").
- Le mode en ligne (bouton "Mode En Ligne").
"""
# ======================
#     CHOIX DU MODE
# ======================

class Mode(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        
        titre = tk.Label(
            self,
            text = "Choisissez votre mode de jeu",
            font = ("Helvetica", 28, "bold"),
            fg = "white",
            bg = "#1e1e1e"
        )
        titre.pack(pady = 100)
        
        # Style des boutons
        btn_font = ("Helvetica", 16, "bold")
        btn_fg = "white"
        btn_bg = "#3a3a3a"
        btn_active = "#505050"

        # Boutons de choix
        btn_local = tk.Button(
            self,
            text = "Mode Local",
            font = btn_font,
            fg = btn_fg,
            bg = btn_bg,
            activebackground = btn_active,
            activeforeground = "white",
            width = 25,
            command = self.on_local 
        )
        
        btn_online = tk.Button(
            self,
            text = "Mode En Ligne",
            font = btn_font,
            fg = btn_fg,
            bg = btn_bg,
            activebackground = btn_active,
            activeforeground = "white",
            width = 25,
            command = self.on_online
        )
            
        btn_retour = tk.Button(
            self,
            text = "← Retour",
            font = btn_font,
            fg = btn_fg,
            bg = btn_bg,
            activebackground = btn_active,
            activeforeground = "white",
            width = 15,
            command = self.on_return
        )
        
        btn_local.pack(pady = 20)
        btn_online.pack(pady = 20)
        btn_retour.pack(pady = 60)

    def on_local(self):
        #Ouvre l'écran de configuration
        self.controller.show_frame("Mapconfig")
    
    def on_online(self):
        #Ouvre l'écran du lobby en ligne
        self.controller.show_frame("OnlineLobby")
    
    def on_return(self):
        #Retour au menu principal
        self.controller.show_frame("Menu")