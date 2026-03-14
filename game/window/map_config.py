# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox
import random

class Mapconfig(tk.Frame):
    """
    Écran de configuration de la carte .

    Cette classe hérite de `tk.Frame` et permet à l'utilisateur de définir le terrain de jeu :
    - Génération procédurale : Création aléatoire d'une carte avec une densité d'obstacles choisie via un slider.
    - Aperçu en temps réel : Visualisation de la carte générée avec des robots de prévisualisation .
    - Gestion de fichiers : Sauvegarde (.txt) et chargement de cartes existantes.
    - Navigation : Retour au choix du mode ou validation pour passer à la configuration des robots.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        
        # Stockage de la carte actuelle
        self.map_data = [] 
        
        # Robots de prévisualisation ---
        self.preview_robots = [] # Liste de dictionnaires {'x', 'y', 'color'}

        # Styles
        label_font = ("Helvetica", 12)
        title_font = ("Helvetica", 24, "bold")
        btn_font = ("Helvetica", 12, "bold")
        
        # En-tête 
        header_frame = tk.Frame(self, bg="#1e1e1e")
        header_frame.pack(pady=10, fill="x")
        tk.Label(header_frame, text="Étape 1 : Configuration du Terrain", font=title_font, fg="white", bg="#1e1e1e").pack()

        # Zone Principale
        main_content = tk.Frame(self, bg="#1e1e1e")
        main_content.pack(expand=True, fill="both", padx=20)

        # Panneau de gauche (Contrôles)
        left_panel = tk.Frame(main_content, bg="#1e1e1e", width=300) 
        left_panel.pack(side="left", fill="y", padx=20)

        # Section Génération
        tk.Label(left_panel, text="--- Génération ---", font=label_font, fg="gray", bg="#1e1e1e").pack(pady=(10, 5))
        
        self.scale_obstacles = tk.Scale(
            left_panel, from_=0, to=20, orient="horizontal", 
            label="Densité d'obstacles (%)", length=250, # Slider un peu plus long
            bg="#1e1e1e", fg="white", font=label_font,
            troughcolor="#505050", highlightthickness=0
        )
        self.scale_obstacles.set(10)
        self.scale_obstacles.pack(pady=5)

        tk.Button(
            left_panel, text="Générer Carte", font=btn_font,
            bg="#0055aa", fg="white", width=20,
            command=self.generer_carte
        ).pack(pady=10)

        # Section Fichier
        tk.Label(left_panel, text="--- Fichier ---", font=label_font, fg="gray", bg="#1e1e1e").pack(pady=(20, 5))

        tk.Button(
            left_panel, text="Sauvegarder Carte", font=btn_font,
            bg="#3a3a3a", fg="white", width=20,
            command=self.sauvegarder_carte
        ).pack(pady=5)

        tk.Button(
            left_panel, text="Charger Carte", font=btn_font,
            bg="#3a3a3a", fg="white", width=20,
            command=self.charger_carte
        ).pack(pady=5)

        # 2. Panneau de droite 
        right_panel = tk.Frame(main_content, bg="#1e1e1e")
        right_panel.pack(side="right", expand=True, fill="both")

        tk.Label(right_panel, text="Aperçu (30x20)", font=label_font, fg="white", bg="#1e1e1e").pack(pady=5)
        
        # Canvas pour l'aperçu de la carte
        self.cell_size = 30 
        self.canvas_width = 30 * self.cell_size 
        self.canvas_height = 20 * self.cell_size 
        
        # Création du Canvas
        self.canvas = tk.Canvas(
            right_panel, width=self.canvas_width, height=self.canvas_height, 
            bg="#777777", highlightthickness=2, highlightbackground="#505050"
        )
        self.canvas.pack()

        # --- Navigation ---
        frame_nav = tk.Frame(self, bg="#1e1e1e")
        frame_nav.pack(side="bottom", fill="x", padx=50, pady=20)

        tk.Button(
            frame_nav, text="← Retour", font=("Helvetica", 14, "bold"),
            fg="white", bg="#3a3a3a", width=15,
            command=self.on_return
        ).pack(side="left")

        tk.Button(
            frame_nav, text="Suivant →", font=("Helvetica", 14, "bold"),
            fg="white", bg="#006400", width=15,
            command=self.aller_suivant
        ).pack(side="right")

        # Lancement
        self.generer_carte()
        
        # Démarrage de l'animation
        self.animate_preview()

    def generer_carte(self):
        """Génère une grille 30x20 avec des obstacles aléatoires"""
        width = 30
        height = 20
        density = self.scale_obstacles.get() / 100.0
        
        self.map_data = [] 
        
        # Parcours de chaque ligne de la grille en hauteur
        for y in range(height):
            row = ""
            # Parcours de chaque colonne de la grille en largeur
            for x in range(width):
                # Si on est sur un bord (première/dernière ligne ou colonne), on place un mur
                if x == 0 or x == width-1 or y == 0 or y == height-1:
                    row += "#"
                else:
                    # Sinon, on place un obstacle aléatoirement selon la densité choisie
                    if random.random() < density:
                        row += "#"
                    else:
                        row += "_"
            self.map_data.append(row)
        
        self.corriger_diagonales_avec_densite(width, height)
        
        # Initialisation des robots sur la nouvelle carte
        self.init_preview_robots()
        self.dessiner_canvas()

    def corriger_diagonales_avec_densite(self, width, height):
        """Supprime les patterns diagonaux tout en conservant la densité"""
        modifie = True
        obstacles_supprimes = 0
        
        # On boucle tant que des modifications sont apportées à la carte
        while modifie:
            modifie = False
            # Parcours de la grille en évitant les bords qui sont toujours des murs
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    # Cas 1 : Diagonale Haut-Gauche vers Bas-Droite bloquante
                    # Pattern recherché :
                    # # _
                    # _ #
                    if (self.map_data[y][x] == '#' and 
                        self.map_data[y][x+1] == '_' and
                        self.map_data[y+1][x] == '_' and 
                        self.map_data[y+1][x+1] == '#'):
                        # On supprime aléatoirement l'un des deux obstacles pour ouvrir le passage
                        if random.random() < 0.5:
                            # Suppression de l'obstacle en haut à gauche
                            self.map_data[y] = self.map_data[y][:x] + '_' + self.map_data[y][x+1:]
                        else:
                            # Suppression de l'obstacle en bas à droite
                            self.map_data[y+1] = self.map_data[y+1][:x+1] + '_' + self.map_data[y+1][x+2:]
                        obstacles_supprimes += 1
                        modifie = True
                    
                    # Cas 2 : Diagonale Haut-Droite vers Bas-Gauche bloquante
                    # Pattern recherché :
                    # _ #
                    # # _
                    elif (self.map_data[y][x] == '_' and 
                        self.map_data[y][x+1] == '#' and
                        self.map_data[y+1][x] == '#' and 
                        self.map_data[y+1][x+1] == '_'):
                        # On supprime aléatoirement l'un des deux obstacles pour ouvrir le passage
                        if random.random() < 0.5:
                            # Suppression de l'obstacle en haut à droite
                            self.map_data[y] = self.map_data[y][:x+1] + '_' + self.map_data[y][x+2:]
                        else:
                            # Suppression de l'obstacle en bas à gauche
                            self.map_data[y+1] = self.map_data[y+1][:x] + '_' + self.map_data[y+1][x+1:]
                        obstacles_supprimes += 1
                        modifie = True
        
        # Pour ne pas fausser la densité choisie par l'utilisateur, 
        # on réintroduit le nombre exact d'obstacles supprimés à des endroits sûrs.
        self.ajouter_obstacles_safe(width, height, obstacles_supprimes)

    def ajouter_obstacles_safe(self, width, height, nombre):
        """Ajoute un nombre donné d'obstacles à des positions sûres"""
        ajoutes = 0
        tentatives = 0
        # Limite de sécurité pour éviter une boucle infinie si la carte est trop pleine
        max_tentatives = nombre * 100
        
        # On continue tant qu'on n'a pas ajouté tous les obstacles requis ou atteint la limite de tentatives
        while ajoutes < nombre and tentatives < max_tentatives:
            tentatives += 1
            
            # Choix d'une position aléatoire en excluant les murs du bord
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            
            # Si la case est actuellement libre
            if self.map_data[y][x] == '_':
                # On vérifie si placer un obstacle ici ne recrée pas une diagonale bloquante
                if self.peut_ajouter_obstacle(x, y, width, height):
                    # Si c'est sûr, on remplace '_' par '#'
                    self.map_data[y] = self.map_data[y][:x] + '#' + self.map_data[y][x+1:]
                    ajoutes += 1

    def peut_ajouter_obstacle(self, x, y, width, height):
        if (x < width - 2 and y < height - 2 and self.map_data[y][x+1] == '_' and self.map_data[y+1][x] == '_' and self.map_data[y+1][x+1] == '#'): return False
        if (x > 0 and y < height - 2 and self.map_data[y][x-1] == '_' and self.map_data[y+1][x-1] == '#' and self.map_data[y+1][x] == '_'): return False
        if (x < width - 2 and y > 0 and self.map_data[y-1][x] == '_' and self.map_data[y-1][x+1] == '#' and self.map_data[y][x+1] == '_'): return False
        if (x > 0 and y > 0 and self.map_data[y-1][x-1] == '#' and self.map_data[y-1][x] == '_' and self.map_data[y][x-1] == '_'): return False
        return True

    # --- MÉTHODES POUR L'ANIMATION ---

    def init_preview_robots(self):
        """Place deux robots (rouge et bleu) sur des cases libres aléatoires"""
        self.preview_robots = []
        # Si aucune carte n'est générée, on ne fait rien
        if not self.map_data: return

        width = len(self.map_data[0])
        height = len(self.map_data)
        colors = ["red", "blue"]

        # Pour chaque couleur de robot
        for color in colors:
            attempts = 0
            # On essaie jusqu'à 100 fois de trouver une case libre aléatoire
            while attempts < 100:
                # Choix d'une position aléatoire (hors murs du bord)
                x = random.randint(1, width - 2)
                y = random.randint(1, height - 2)
                
                # Si la case est libre ('_')
                if self.map_data[y][x] == '_':
                    # On ajoute le robot à la liste
                    self.preview_robots.append({'x': x, 'y': y, 'color': color})
                    break
                attempts += 1

    def animate_preview(self):
        """Deplace les robots aléatoirement sur la carte"""
        if self.map_data and self.preview_robots:
            for robot in self.preview_robots:
                # Déplacement aléatoire (H, B, G, D)
                moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                valid_moves = []
                
                for dx, dy in moves:
                    nx, ny = robot['x'] + dx, robot['y'] + dy
                    # Vérifier limites et obstacles
                    if 0 <= ny < len(self.map_data) and 0 <= nx < len(self.map_data[0]):
                        if self.map_data[ny][nx] == '_':
                            valid_moves.append((nx, ny))
                
                if valid_moves:
                    nx, ny = random.choice(valid_moves)
                    robot['x'] = nx
                    robot['y'] = ny
            
            # Redessiner le canvas avec les nouvelles positions
            self.dessiner_canvas()
        
        # Rappeler cette fonction dans 400ms
        self.after(400, self.animate_preview)

    def dessiner_canvas(self):
        """Dessine self.map_data et les robots sur le Canvas"""
        # 1. Nettoyage du canvas avant de redessiner
        self.canvas.delete("all") 
        
        # Si pas de carte, on ne fait rien
        if not self.map_data: return

        # 2. Dessin du quadrillage 
        # Lignes verticales
        for x in range(0, self.canvas_width + 1, self.cell_size):
            self.canvas.create_line(x, 0, x, self.canvas_height, fill="#505050")
        # Lignes horizontales
        for y in range(0, self.canvas_height + 1, self.cell_size):
            self.canvas.create_line(0, y, self.canvas_width, y, fill="#505050")

        # 3. Dessin des obstacles (Murs)
        # On parcourt chaque case de la grille
        for y, row in enumerate(self.map_data):
            for x, char in enumerate(row):
                # Si le caractère est '#', c'est un obstacle
                if char == "#":
                    # Calcul des coordonnées en pixels du rectangle
                    x1 = x * self.cell_size
                    y1 = y * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    # Dessin du rectangle noir
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
        
        # 4. Dessin des robots de prévisualisation (Cercles colorés)
        for robot in self.preview_robots:
            # Calcul des coordonnées de la case du robot
            x1 = robot['x'] * self.cell_size
            y1 = robot['y'] * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            
            # Dessin d'un cercle un peu plus petit que la case 
            margin = 4 
            self.canvas.create_oval(x1 + margin, y1 + margin, x2 - margin, y2 - margin, fill=robot['color'], outline="white", width=1)

    def sauvegarder_carte(self):
        if not self.map_data: return
        filepath = filedialog.asksaveasfilename(title="Sauvegarder", defaultextension=".txt", filetypes=[("Texte", "*.txt")])
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    for row in self.map_data: f.write(row + "\n")
                messagebox.showinfo("Succès", "Carte sauvegardée !")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {e}")

    def charger_carte(self):
        filepath = filedialog.askopenfilename(title="Charger", filetypes=[("Texte", "*.txt")])
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f: lines = [line.strip() for line in f.readlines()]
                if len(lines) != 20 or any(len(line) != 30 for line in lines):
                    messagebox.showwarning("Erreur", "Dimensions incorrectes (doit être 30x20).")
                    return
                self.map_data = lines
                self.init_preview_robots() # Réinitialiser les robots sur la nouvelle carte
                self.dessiner_canvas()
                messagebox.showinfo("Succès", "Carte chargée !")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {e}")

    def aller_suivant(self):
        if not self.map_data:
            messagebox.showwarning("Attention", "Générez une carte d'abord.")
            return

        self.controller.parametres_partie["map_data"] = self.map_data
        self.controller.parametres_partie["densite_obstacles"] = self.scale_obstacles.get()
        print("Carte validée.")
        
        self.controller.show_frame("Configuration")
    
    def on_return(self):
        #Retour au menu principal
        self.controller.show_frame("Mode")