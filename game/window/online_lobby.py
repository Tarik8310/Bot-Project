import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os

# Ajouter le dossier parent au path pour importer client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validator import valider_programme_robot


try:
    from network.client import GameClient
except ImportError:
    GameClient = None
    print("⚠️ Module client réseau non trouvé")

class OnlineLobby(tk.Frame):
    """
    Salle d'attente pour une partie en ligne
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        self.client = None
        self.robot_program = None
        self.robot_name = "Mon Robot"
        
        # Styles
        title_font = ("Helvetica", 24, "bold")
        label_font = ("Helvetica", 12)
        
        # Titre
        tk.Label(
            self,
            text="🌐 PARTIE EN LIGNE 🌐",
            font=title_font,
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=20)
        
        # --- Connexion au serveur ---
        connection_frame = tk.Frame(self, bg="#1e1e1e")
        connection_frame.pack(pady=20)
        
        tk.Label(
            connection_frame,
            text="Adresse du serveur:",
            font=label_font,
            fg="white",
            bg="#1e1e1e"
        ).grid(row=0, column=0, padx=5)
        
        self.entry_host = tk.Entry(
            connection_frame,
            font=label_font,
            width=20,
            bg="#2b2b2b",
            fg="white",
            insertbackground="white"
        )
        self.entry_host.insert(0, "localhost")
        self.entry_host.grid(row=0, column=1, padx=5)
        
        tk.Label(
            connection_frame,
            text="Port:",
            font=label_font,
            fg="white",
            bg="#1e1e1e"
        ).grid(row=0, column=2, padx=5)
        
        self.entry_port = tk.Entry(
            connection_frame,
            font=label_font,
            width=8,
            bg="#2b2b2b",
            fg="white",
            insertbackground="white"
        )
        self.entry_port.insert(0, "5555")
        self.entry_port.grid(row=0, column=3, padx=5)
        
        self.btn_connect = tk.Button(
            connection_frame,
            text="Se Connecter",
            font=("Helvetica", 12, "bold"),
            bg="#0055aa",
            fg="white",
            width=15,
            command=self.connect_to_server
        )
        self.btn_connect.grid(row=0, column=4, padx=10)
        
        # --- Statut de connexion ---
        self.lbl_status = tk.Label(
            self,
            text="❌ Non connecté",
            font=("Helvetica", 14),
            fg="red",
            bg="#1e1e1e"
        )
        self.lbl_status.pack(pady=10)
        
        # --- Sélection du robot ---
        robot_frame = tk.Frame(self, bg="#1e1e1e")
        robot_frame.pack(pady=20)
        
        tk.Label(
            robot_frame,
            text="Votre Robot:",
            font=label_font,
            fg="white",
            bg="#1e1e1e"
        ).grid(row=0, column=0, padx=10)
        
        self.entry_name = tk.Entry(
            robot_frame,
            font=label_font,
            width=15,
            bg="#2b2b2b",
            fg="white",
            insertbackground="white"
        )
        self.entry_name.insert(0, self.robot_name)
        self.entry_name.grid(row=0, column=1, padx=5)
        
        self.btn_load_robot = tk.Button(
            robot_frame,
            text="Charger Programme (.rbt)",
            font=("Helvetica", 11, "bold"),
            bg="#3a3a3a",
            fg="white",
            command=self.load_robot_program,
            state="disabled"
        )
        self.btn_load_robot.grid(row=0, column=2, padx=10)
        
        # --- Liste des joueurs ---
        tk.Label(
            self,
            text="👥 Joueurs dans la salle",
            font=("Helvetica", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=10)
        
        self.listbox_players = tk.Listbox(
            self,
            bg="#2b2b2b",
            fg="white",
            font=("Courier", 11),
            height=6,
            width=50
        )
        self.listbox_players.pack(pady=10)
        
        # --- Bouton prêt / démarrer ---
        self.btn_ready = tk.Button(
            self,
            text="✅ Je suis prêt!",
            font=("Helvetica", 14, "bold"),
            bg="#006400",
            fg="white",
            width=20,
            command=self.mark_ready,
            state="disabled"
        )
        self.btn_ready.pack(pady=20)
        
        # --- Navigation ---
        nav_frame = tk.Frame(self, bg="#1e1e1e")
        nav_frame.pack(side="bottom", fill="x", padx=50, pady=20)
        
        tk.Button(
            nav_frame,
            text="← Retour",
            font=("Helvetica", 14, "bold"),
            fg="white",
            bg="#3a3a3a",
            width=15,
            command=self.return_to_menu
        ).pack(side="left")
    
    def tkraise(self, aboveThis=None):
        """Appelé quand cette frame devient visible"""
        super().tkraise(aboveThis)
        self.reset_ui()
    
    def connect_to_server(self):
        """Tente de se connecter au serveur"""
        if GameClient is None:
            messagebox.showerror(
                "Erreur",
                "Module réseau non disponible.\n"
                "Assurez-vous que network/client.py existe."
            )
            return
            
        host = self.entry_host.get().strip()
        port_str = self.entry_port.get().strip()
        
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Erreur", "Port invalide")
            return
            
        # Créer le client
        self.client = GameClient()
        
        # Définir les callbacks
        self.client.set_callback('on_connect', self.on_connect)
        self.client.set_callback('on_player_ready', self.on_player_ready)
        self.client.set_callback('on_game_start', self.on_game_start)
        self.client.set_callback('on_disconnect', self.on_disconnect)
        
        # Tenter la connexion
        if self.client.connect(host, port):
            self.lbl_status.config(text="✅ Connecté au serveur", fg="green")
            self.btn_connect.config(state="disabled")
            self.btn_load_robot.config(state="normal")
            
            # 🔧 FIX: Sauvegarder le client dès la connexion
            self.controller.parametres_partie['online_client'] = self.client
        else:
            messagebox.showerror("Erreur", "Impossible de se connecter au serveur")
            self.client = None
            
    def on_connect(self, message):
        """Callback quand la connexion est établie"""
        def update_ui():
            players_count = message.get('players_count', 1)
            self.listbox_players.delete(0, tk.END)
            self.listbox_players.insert(tk.END, f"👤 Vous (Client {self.client.client_id})")
            for i in range(players_count - 1):
                self.listbox_players.insert(tk.END, f"👤 Joueur en attente...")
        
        self.after(0, update_ui)
        
    def load_robot_program(self):
        """Charge un fichier .rbt"""
        filepath = filedialog.askopenfilename(
            title="Choisir votre robot",
            filetypes=[("Fichiers Robot", "*.rbt")]
        )
        
        if not filepath:
            return
        
        # Validation avec la fonction centralisée
        valide, programme, erreur = valider_programme_robot(filepath)
        
        if not valide:
            messagebox.showwarning(
                "Code invalide",
                f"Le fichier contient une erreur :\n{erreur}"
            )
            return
        
        # Programme valide
        self.robot_program = programme
        self.robot_name = self.entry_name.get().strip() or "Robot"
        
        print(f"Programme chargé: {self.robot_program}")
        
        messagebox.showinfo(
            "Robot chargé",
            f"Programme chargé: {len(self.robot_program)} instructions\n"
            f"Nom: {self.robot_name}"
        )
        
        self.btn_ready.config(state="normal")
           
            
            
    def mark_ready(self):
        """Marque le joueur comme prêt"""
        if not self.client:
            messagebox.showerror("Erreur", "Non connecté au serveur")
            return
            
        if not self.robot_program:
            messagebox.showerror("Erreur", "Aucun programme chargé")
            return
        
        print(f"📤 Envoi du programme au serveur...")
        print(f"   Nom: {self.robot_name}")
        print(f"   Programme: {self.robot_program[:3]}...")
        
        # Envoyer le programme au serveur
        success = self.client.send_robot_program(self.robot_program, self.robot_name)
        
        if not(success):
            self.btn_ready.config(state="disabled", text="⏳ En attente...")
            print("✅ Programme envoyé avec succès")
            
            messagebox.showinfo(
                "Prêt",
                "Votre robot est prêt!\nEn attente des autres joueurs..."
            )
        else:
            messagebox.showerror("Erreur", "Impossible d'envoyer le programme")
        
    def on_player_ready(self, message):
        """Callback quand un joueur devient prêt"""
        def update_ui():
            ready_count = message.get('ready_count', 0)
            self.lbl_status.config(
                text=f"✅ {ready_count} joueur(s) prêt(s)",
                fg="yellow"
            )
        
        self.after(0, update_ui)
        
    def on_game_start(self, state):
        """Callback quand la partie démarre"""
        def start_game():
            messagebox.showinfo("Début", "La partie commence!")
            # 🔧 FIX: Le client est déjà sauvegardé dans connect_to_server
            # On met juste à jour l'état
            self.controller.parametres_partie['online_state'] = state
            self.controller.show_frame("OnlineGameplay")
        
        self.after(0, start_game)
        
    def on_disconnect(self):
        """Callback en cas de déconnexion"""
        def update_ui():
            self.lbl_status.config(text="❌ Déconnecté", fg="red")
            self.btn_connect.config(state="normal")
            self.btn_load_robot.config(state="disabled")
            self.btn_ready.config(state="disabled", text="✅ Je suis prêt!")
            messagebox.showwarning("Déconnexion", "Connexion perdue avec le serveur")
        
        self.after(0, update_ui)

    def reset_ui(self):
        """Réinitialise l'affichage de la salle d'attente"""
        # 🔧 FIX: Ne pas déconnecter le client s'il existe déjà
        # On garde la connexion active
        
        self.lbl_status.config(text="❌ Non connecté", fg="red")
        self.listbox_players.delete(0, tk.END)
        self.listbox_players.insert(tk.END, "Aucun joueur connecté")

        # Réinitialiser info robot
        self.robot_program = None
        self.robot_name = "Mon Robot"
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, self.robot_name)

        # Boutons
        self.btn_connect.config(state="normal")
        self.btn_load_robot.config(state="disabled")
        self.btn_ready.config(state="disabled", text="✅ Je suis prêt!")
        
    def return_to_menu(self):
        """Retour au menu"""
        if self.client:
            self.client.disconnect()
            self.client = None
        self.controller.show_frame("Mode")