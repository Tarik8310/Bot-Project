"""
Fichier définissant l'écran de jeu en ligne (mode Spectateur/Client).

Ce module gère l'affichage et la synchronisation de la partie lorsqu'elle est jouée en réseau.
Contrairement au mode local, ce mode ne calcule pas la logique du jeu (déplacements, tirs, etc.)
mais reçoit l'état du jeu envoyé par le serveur à chaque tour.

Fonctionnalités principales :
- Réception et affichage des mises à jour du serveur (Carte, Robots, Logs).
- Conversion des données brutes du serveur en format compatible avec l'affichage local.
- Gestion des événements réseaux (Déconnexion, Fin de partie).
- Interface simplifiée
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ajout du chemin parent pour importer les modules de base
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from base_gameplay import BaseGameplay

class OnlineGameplay(BaseGameplay):
    """
    Classe gérant l'affichage du jeu en mode Online.
    Hérite de `BaseGameplay` pour réutiliser l'interface graphique (Canvas, Stats, Logs).

    En mode Online, cette classe agit comme un "terminal passif" : elle ne prend aucune
    décision sur le jeu, elle se contente d'afficher ce que le serveur lui dicte.
    """
    
    def __init__(self, parent, controller):
        """
        Initialise l'écran de jeu en ligne.

        Args:
            parent (tk.Widget): Le conteneur parent.
            controller (App): Le contrôleur principal de l'application.
        """
        self.client = None      # Instance du client réseau (socket)
        self.game_state = None  # État actuel du jeu reçu du serveur
        
        super().__init__(parent, controller)
        
        # Personnalisation de l'interface pour le mode en ligne
        self.lbl_title.config(text="🌐 COMBAT EN LIGNE 🌐")
        self.lbl_status.config(text="🌐 Connecté", fg="green")
    
    def setup_controls(self):
        """
        Configure les contrôles spécifiques au mode online.
        Ici, pas de bouton Pause ou Vitesse, seul un bouton Quitter est disponible
        car le joueur est spectateur du serveur.
        """
        tk.Button(
            self.control_frame, 
            text="🛑 Quitter", 
            font=("Helvetica", 12, "bold"),
            fg="white", 
            bg="#8B0000", 
            width=12,
            command=self.quit_game
        ).pack(pady=5)
    
    def tkraise(self, aboveThis=None):
        """
        Méthode appelée lorsque la fenêtre passe au premier plan.
        Déclenche l'initialisation de la connexion et de l'affichage.
        """
        super().tkraise(aboveThis)
        self.initialize_online_game()
    
    def initialize_online_game(self):
        """
        Initialise la partie en récupérant les données du contrôleur.
        Configure les callbacks (fonctions de rappel) pour réagir aux messages du serveur.
        """
        params = self.controller.parametres_partie
        
        # Récupération de l'objet client réseau stocké par le Lobby
        self.client = params.get('online_client')
        
        if not self.client:
            print("❌ ERREUR: Client réseau non trouvé")
            messagebox.showerror("Erreur", "Connexion au serveur perdue.\nRetour au menu.")
            self.controller.show_frame("Menu") 
            return

        # Configuration des écouteurs d'événements réseau
        # Quand le serveur envoie un log -> on appelle self.on_log
        # Quand le serveur envoie un tour -> on appelle self.on_turn_update
        # etc.
        self.client.set_callback('on_log', self.on_log)
        self.client.set_callback('on_turn_update', self.on_turn_update)
        self.client.set_callback('on_game_end', self.on_game_end)
        self.client.set_callback('on_disconnect', self.on_disconnect)
        
        # Chargement de l'état initial du jeu (reçu lors de la connexion)
        self.game_state = params.get('online_state', {})
        
        # Initialisation des robots locaux pour l'affichage des stats
        robots = self.game_state.get('robots', [])
        if robots:
            for robot in robots:
                # Si l'énergie max n'est pas fournie, on suppose qu'elle est égale à l'énergie actuelle
                if 'max_energie' not in robot:
                    robot['max_energie'] = robot.get('energie', 1500)
        
        # Création des barres de vie
        self.create_stats_widgets(robots)
        
        # Conversion et affichage de la carte initiale
        raw_map = self.game_state.get('map', [])
        display_map = self.convert_server_map(raw_map)
        
        self.draw_map(display_map, robots)
        self.update_stats(robots)

    def convert_server_map(self, server_map):
        """
        Convertit la carte reçue du serveur (format texte) vers le format interne
        utilisé par `draw_map` (format numérique/mixte).

        Le serveur envoie : ["####____", "____####"]
        L'affichage attend : [[1,1,1,1,0,0,0,0], [0,0,0,0,1,1,1,1]]

        Args:
            server_map (list): Liste de chaînes de caractères représentant la grille.

        Returns:
            list: Matrice 2D où 1=Mur, 0=Vide, 'Mine'=Mine.
        """
        result = []
        for row in server_map:
            converted_row = []
            for char in row:
                if char == '#':
                    converted_row.append(1)  # Obstacle
                elif char == 'M' or char == 'Mine':
                    converted_row.append('Mine')  # Mine
                else:
                    converted_row.append(0)  # Vide
            result.append(converted_row)
        return result

    def on_log(self, message):
        """
        Callback exécuté à la réception d'un message de log du serveur.
        Affiche le texte dans la console de l'interface graphique.
        """
        def update_log():
            text = message.get('text', '')
            if text:
                self.log_text.insert(tk.END, text + "\n")
                self.log_text.see(tk.END) # Scroll automatique vers le bas
                # Debug console
                print(f"[CLIENT LOG] {text}", file=sys.__stdout__)
        
        # Utilisation de after() pour garantir l'exécution dans le thread principal de l'UI
        self.after(0, update_log)
    
    def on_turn_update(self, message):
        """
        Callback exécuté à chaque nouveau tour de jeu.
        Met à jour la carte, les positions des robots, et les statistiques.
        """
        def update():
            # Extraction des nouvelles données
            self.current_turn = message.get('turn', 0)
            robots = message.get('robots', [])
            raw_map = message.get('map', [])
            
            # Mise à jour de l'état local
            self.game_state['robots'] = robots
            self.game_state['turn'] = self.current_turn
            
            # Conversion de la carte
            display_map = self.convert_server_map(raw_map)
            
            # Gestion des mines : le serveur envoie les mines séparément ou dans la map
            # Ici on s'assure d'afficher les mines connues des robots
            for robot in robots:
                mines = robot.get('mines', [])
                for mine_pos in mines:
                    try:
                        my, mx = int(mine_pos[0]), int(mine_pos[1])
                        if 0 <= my < len(display_map) and 0 <= mx < len(display_map[0]):
                            display_map[my][mx] = 'Mine'
                    except Exception as e:
                        print(f"Erreur mine: {e}")

            # Rafraîchissement de l'interface
            self.lbl_turn.config(text=f"Tour: {self.current_turn}")
            self.draw_map(display_map, robots)
            self.update_stats(robots)
        
        self.after(0, update)

    def on_game_end(self, message):
        """
        Callback exécuté lorsque la partie est terminée.
        Affiche une popup avec le résultat et déconnecte le client.
        """
        def show_end():
            winner = message.get('winner')
            turn = message.get('turn', 0)
            
            if winner:
                messagebox.showinfo(
                    "Victoire!",
                    f"🏆 {winner['name']} remporte la victoire!\n\n"
                    f"Énergie restante: {winner['energie']}\n"
                    f"Tours joués: {turn}"
                )
            else:
                messagebox.showinfo(
                    "Match nul",
                    f"⚔️ Égalité! Tous les robots sont hors-jeu.\n\n"
                    f"Tours joués: {turn}"
                )
            
            # Déconnexion propre
            if self.client:
                self.lbl_status.config(text="❌ Déconnecté", fg="red")
                self.client.disconnect()
            
            # Retour au menu
            self.controller.show_frame("Menu")
        
        self.after(0, show_end)

    def on_disconnect(self):
        """
        Callback exécuté si la connexion au serveur est perdue inopinément.
        """
        def show_disconnect():
            self.lbl_status.config(text="❌ Déconnecté", fg="red")
            messagebox.showwarning("Déconnexion", "Connexion perdue avec le serveur")
            self.controller.show_frame("Menu")
        
        self.after(0, show_disconnect)

    def quit_game(self):
        """
        Gère le clic sur le bouton 'Quitter'.
        Demande confirmation et ferme la connexion.
        """
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter la partie?"):
            if self.client:
                self.client.disconnect()
            self.controller.show_frame("Menu")