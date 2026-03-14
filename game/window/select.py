from tkinter import filedialog, messagebox
import tkinter as tk
import sys
import os

# --- Importation du validateur externe ---
# On ajoute le dossier parent (racine) au path pour trouver validator.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validator import valider_programme_robot

class Selection(tk.Frame):
    """
    Étape 3 : Sélection des fichiers Robots (.rbt) avec Icônes et Aperçu
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        
        self.robot_files = []
        self.programmes_robots = {}
        self.selected_widget = None 

        # Couleurs fixes pour les robots
        self.robot_colors = ["#FF0000", "#0000FF", "#00FF00", "#FFFF00", "#FF00FF", "#00FFFF"]

        # Styles
        label_font = ("Helvetica", 14)
        title_font = ("Helvetica", 28, "bold")

        # --- Titre ---
        tk.Label(
            self, 
            text="Étape 3 : Choix des Robots", 
            font=title_font, fg="white", bg="#1e1e1e"
        ).pack(pady=(20, 10))
        
        # --- Zone d'info et Bouton Chargement (Haut) ---
        top_controls = tk.Frame(self, bg="#1e1e1e")
        top_controls.pack(pady=10)

        self.lbl_info = tk.Label(
            top_controls, 
            text="Veuillez sélectionner les programmes...", 
            font=label_font, fg="gray", bg="#1e1e1e"
        )
        self.lbl_info.pack(side="left", padx=10)

        tk.Button(
            top_controls, text="Charger les fichiers (.rbt)", font=("Helvetica", 12, "bold"),
            bg="#0055aa", fg="white", command=self.charger_fichiers
        ).pack(side="left", padx=10)

        # --- Conteneur Principal (Milieu) : Liste + Aperçu côte à côte ---
        content_frame = tk.Frame(self, bg="#1e1e1e")
        content_frame.pack(expand=True, fill="both", padx=50, pady=10)

        # 1. Panneau Gauche : Liste des robots (Scrollable Canvas pour les icônes)
        left_panel = tk.Frame(content_frame, bg="#1e1e1e")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left_panel, text="Fichiers chargés :", 
            font=("Helvetica", 12), fg="white", bg="#1e1e1e", anchor="w"
        ).pack(fill="x", pady=(0, 5))

        # Configuration du scroll pour la liste personnalisée
        self.canvas_list = tk.Canvas(left_panel, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.scrollbar_list = tk.Scrollbar(left_panel, orient="vertical", command=self.canvas_list.yview)
        
        # Frame interne qui contiendra les items
        self.robots_list_frame = tk.Frame(self.canvas_list, bg="#2b2b2b")
        
        # Lien entre le canvas et la frame interne (Mise à jour scrollregion uniquement)
        self.robots_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas_list.configure(scrollregion=self.canvas_list.bbox("all"))
        )
        self.canvas_window = self.canvas_list.create_window((0, 0), window=self.robots_list_frame, anchor="nw")
        
        # Redimensionnement de la frame interne quand le canvas change de taille
        self.canvas_list.bind(
            "<Configure>",
            lambda e: self.canvas_list.itemconfig(self.canvas_window, width=e.width)
        )

        self.canvas_list.configure(yscrollcommand=self.scrollbar_list.set)

        self.canvas_list.pack(side="left", fill="both", expand=True)
        self.scrollbar_list.pack(side="right", fill="y")

        # 2. Panneau Droit : Aperçu du code
        right_panel = tk.Frame(content_frame, bg="#1e1e1e")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            right_panel, text="Aperçu du code :", 
            font=("Helvetica", 12), fg="white", bg="#1e1e1e", anchor="w"
        ).pack(fill="x", pady=(0, 5))

        self.text_preview = tk.Text(
            right_panel,
            bg="#2b2b2b", fg="#00ff00",
            font=("Courier", 16), # Augmenté encore (16)
            state="disabled",
            width=40 
        )
        scrollbar_preview = tk.Scrollbar(right_panel, command=self.text_preview.yview)
        self.text_preview.configure(yscrollcommand=scrollbar_preview.set)
        
        self.text_preview.pack(side="left", fill="both", expand=True)
        scrollbar_preview.pack(side="right", fill="y")

        # --- Navigation (Bas) ---
        frame_nav = tk.Frame(self, bg="#1e1e1e")
        frame_nav.pack(side="bottom", fill="x", padx=50, pady=30)

        # Bouton Retour
        tk.Button(
            frame_nav, text="← Retour", font=("Helvetica", 14, "bold"),
            fg="white", bg="#3a3a3a", width=15,
            command=lambda: controller.show_frame("Configuration") 
        ).pack(side="left")

        # Bouton LANCER
        tk.Button(
            frame_nav, text="LANCER LE COMBAT !", font=("Helvetica", 16, "bold"),
            fg="white", bg="#8B0000", width=20,
            command=self.lancer_jeu
        ).pack(side="right")

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        nb = self.controller.parametres_partie.get("nb_robots", 2)
        self.lbl_info.config(text=f"Veuillez sélectionner {nb} fichiers robots (.rbt)")
    
    # --- Gestion de la liste personnalisée avec Icônes ---

    def creer_item_robot(self, index, nom_fichier):
        """Crée un widget visuel (Frame) pour un robot dans la liste"""
        color = self.robot_colors[index % len(self.robot_colors)]
        
        # Frame conteneur pour une ligne (Item)
        item_frame = tk.Frame(self.robots_list_frame, bg="#2b2b2b", pady=5, padx=5, bd=1, relief="flat")
        item_frame.pack(fill="x", pady=2, padx=2)
        
        # 1. Icône (Canvas)
        icon_canvas = tk.Canvas(item_frame, width=40, height=40, bg="#2b2b2b", highlightthickness=0)
        icon_canvas.pack(side="left", padx=(0, 10))
        
        # Dessin du robot stylisé
        # Corps
        icon_canvas.create_rectangle(8, 12, 32, 36, fill=color, outline="white", width=1)
        # Yeux
        icon_canvas.create_rectangle(12, 18, 18, 22, fill="white", outline="black") 
        icon_canvas.create_rectangle(22, 18, 28, 22, fill="white", outline="black") 
        # Antenne
        icon_canvas.create_line(20, 12, 20, 5, fill="white", width=1)
        icon_canvas.create_oval(18, 3, 22, 7, fill="red", outline="red") 

        # 2. Nom du fichier
        lbl_name = tk.Label(
            item_frame, 
            text=f"R{index+1} : {nom_fichier}", 
            font=("Helvetica", 12, "bold"), 
            bg="#2b2b2b", fg="white", anchor="w"
        )
        lbl_name.pack(side="left", fill="x", expand=True)

        # Bindings pour la sélection (clic partout)
        # On utilise une fonction lambda avec des valeurs par défaut pour capturer l'état actuel
        for widget in (item_frame, icon_canvas, lbl_name):
            widget.bind("<Button-1>", lambda e, f=nom_fichier, w=item_frame: self.on_select_robot(f, w))
            widget.configure(cursor="hand2")
            
        return item_frame 

    def on_select_robot(self, nom_fichier, widget_frame):
        """Gestion du clic sur un robot"""
        # Reset visuel de l'ancien sélectionné
        if self.selected_widget:
            try:
                self.selected_widget.config(bg="#2b2b2b")
                for child in self.selected_widget.winfo_children():
                    child.config(bg="#2b2b2b")
            except:
                pass # Le widget a peut-être été détruit lors d'un rechargement

        # Mise en valeur du nouveau sélectionné (Gris clair)
        self.selected_widget = widget_frame
        selection_color = "#404040" 
        widget_frame.config(bg=selection_color)
        for child in widget_frame.winfo_children():
            child.config(bg=selection_color)

        self.afficher_apercu(nom_fichier)

    def afficher_apercu(self, nom_fichier):
        """Affiche le code dans la zone de texte à droite"""
        self.text_preview.config(state="normal")
        self.text_preview.delete("1.0", tk.END)
        
        if nom_fichier in self.programmes_robots:
            programme = self.programmes_robots[nom_fichier]
            for i, line in enumerate(programme):
                # Affichage propre avec numéro de ligne
                self.text_preview.insert(tk.END, f"{i+1:02d} | {line}\n")
        
        self.text_preview.config(state="disabled")

    def charger_fichiers(self):
        nb = self.controller.parametres_partie.get("nb_robots", 2)
        
        files = filedialog.askopenfilenames(
            title=f"Choisir {nb} robots", 
            filetypes=[("Fichiers Robot", "*.rbt")]
        )
        
        if not files: return
        
        if len(files) != nb:
            messagebox.showwarning(
                "Attention", 
                f"Il faut exactement {nb} fichiers (vous en avez sélectionné {len(files)})."
            )
            return

        # --- UTILISATION DU VALIDATEUR EXTERNE ---
        for fpath in files:
            nom_fichier = fpath.split("/")[-1]
            
            # Appel à la fonction importée de validator.py
            valide, programme, erreur = valider_programme_robot(fpath)
            
            if not valide:
                messagebox.showwarning("Code invalide", f"Le fichier {nom_fichier} contient une erreur :\n{erreur}")
                return

        # Si tout est valide, on charge
        self.robot_files = list(files)
        self.programmes_robots = {}

        # Nettoyage liste visuelle
        for widget in self.robots_list_frame.winfo_children():
            widget.destroy()
        self.selected_widget = None
        
        # Reset aperçu
        self.text_preview.config(state="normal")
        self.text_preview.delete("1.0", tk.END)
        self.text_preview.config(state="disabled")

        # Création des items visuels
        first_widget = None
        first_name = ""
        
        for index, fpath in enumerate(self.robot_files):
            nom_fichier = fpath.split("/")[-1]
            
            # On relit le programme validé
            _, programme, _ = valider_programme_robot(fpath)
            self.programmes_robots[nom_fichier] = programme
            
            # Création de l'icône et du label
            w = self.creer_item_robot(index, nom_fichier)
            if index == 0: 
                first_widget = w
                first_name = nom_fichier

        # Auto-sélection du premier robot
        if first_widget and first_name:
            self.on_select_robot(first_name, first_widget)

        self.lbl_info.config(text="Tous les robots sont prêts !", fg="#00FF00")

    def lancer_jeu(self):
        nb = self.controller.parametres_partie.get("nb_robots", 2)
        if len(self.robot_files) != nb :
            messagebox.showerror("Erreur", "Veuillez charger le bon nombre de robots.")
            return

        self.controller.parametres_partie["robots_files"] = self.robot_files
        self.controller.show_frame("Gameplay")