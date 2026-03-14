import tkinter as tk 
from tkinter import messagebox 
import threading  # Module pour exécuter la boucle de jeu en parallèle de l'interface (évite le gel)
import time  # Module pour gérer le temps et les pauses (vitesse du jeu)
import sys 
import os 
import random 

# Gestion des imports pour trouver robots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from robotdoc import Robot, couts

# --- Classe utilitaire pour les logs --- 
# Classe générée par l'IA
class RedirectText:
    """
    Redirige les flux de sortie standard vers un widget Tkinter Text.
    Cela permet d'afficher les print() du jeu directement dans l'interface graphique.
    """
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout

    def write(self, string):
        try:
            self.text_widget.insert(tk.END, string)
            self.text_widget.see(tk.END) # Auto-scroll vers le bas
        except Exception:
            pass

    def flush(self):
        pass

class Gameplay(tk.Frame):
    """
    Écran principal du jeu.

    Cette classe gère toute la logique d'affichage et d'exécution de la partie :
    - Initialisation de la carte et des robots à partir des paramètres du contrôleur.
    - Boucle de jeu (Game Loop) exécutée dans un thread séparé pour ne pas bloquer l'interface.
    - Rendu graphique : Carte, Obstacles, Robots, Mines, Tirs laser.
    - Gestion des événements : Pause, Changement de vitesse, Arrêt de la partie.
    - Affichage des statistiques en temps réel (Barres de vie, Logs).
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        
        # État du jeu
        self.map_jeu = [] # Carte sous forme de liste 2D
        self.tous_les_robots = [] # Liste des instances de robots
        self.game_running = False
        self.game_paused = False
        self.current_turn = 0
        
        # Redirection des logs
        self.redirector = None
        
        # Gestion de la vitesse 
        self.base_delay = 0.2  # Délai de base (0.2s)
        self.speed_multipliers = [0.5, 1.0, 1.5, 2.0]
        self.current_speed_index = 1 # Vitesse x1.0 par défaut
        
        # Stockage des références UI pour mise à jour rapide
        self.robot_ui_elements = {}
        
        # Paramètres visuels
        self.cell_size = 25
        self.canvas_width = 30 * self.cell_size
        self.canvas_height = 20 * self.cell_size
        
        # Palette de couleurs pour les robots
        self.robot_colors = {
            "R1": "#FF0000",
            "R2": "#0000FF", 
            "R3": "#00FF00",
            "R4": "#FFFF00", 
            "R5": "#FF00FF",
            "R6": "#00FFFF",
        }
        
        # Construction de l'interface
        self.setup_ui()
        
    def setup_ui(self):
        """Construit l'interface graphique complète du gameplay."""
        # Titre
        title_frame = tk.Frame(self, bg="#1e1e1e")
        title_frame.pack(pady=10)
        
        tk.Label(
            title_frame, 
            text="🤖 COMBAT EN COURS 🤖", 
            font=("Helvetica", 24, "bold"),
            fg="white", 
            bg="#1e1e1e"
        ).pack()
        
        # Zone principale
        content_frame = tk.Frame(self, bg="#1e1e1e")
        content_frame.pack(expand=True, fill="both", padx=20)
        
        # Panneau Gauche (Canvas + Logs)
        left_panel = tk.Frame(content_frame, bg="#1e1e1e")
        left_panel.pack(side="left", padx=10, fill="both", expand=True)
        
        # 1. Canvas de Jeu
        self.canvas = tk.Canvas(
            left_panel, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg="#777777", 
            highlightthickness=2, 
            highlightbackground="#505050"
        )
        self.canvas.pack(pady=(0, 10))
        
        # 2. Zone de Logs
        log_frame = tk.Frame(left_panel, bg="#1e1e1e")
        log_frame.pack(fill="both", expand=True)
        
        tk.Label(
            log_frame, 
            text="📜 Journal de combat", 
            font=("Helvetica", 12, "bold"), 
            fg="#ffaa00", 
            bg="#1e1e1e", 
            anchor="w"
        ).pack(fill="x")
        
        self.log_text = tk.Text(
            log_frame, 
            height=8, 
            bg="black", 
            fg="#00ff00", 
            font=("Consolas", 9),
            state="normal"
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Panneau Droit avec Stats et Contrôles
        right_panel = tk.Frame(content_frame, bg="#1e1e1e", width=350)
        right_panel.pack(side="right", fill="y", padx=10)
        
        # Compteur de tours
        self.lbl_turn = tk.Label(
            right_panel, 
            text="Tour: 0", 
            font=("Helvetica", 16, "bold"),
            fg="yellow", 
            bg="#1e1e1e"
        )
        self.lbl_turn.pack(pady=10)
        
        # Titre Stats
        tk.Label(
            right_panel, 
            text="📊 Énergie des Robots", 
            font=("Helvetica", 14, "bold"),
            fg="white", 
            bg="#1e1e1e"
        ).pack(pady=(5, 10))
        
        # Conteneur des barres de vie
        self.stats_container = tk.Frame(right_panel, bg="#1e1e1e")
        self.stats_container.pack(pady=10, fill="x")
        
        # Boutons de contrôle
        control_frame = tk.Frame(right_panel, bg="#1e1e1e")
        control_frame.pack(pady=20, side="bottom")
        
        # Bouton Vitesse
        current_speed = self.speed_multipliers[self.current_speed_index]
        self.btn_speed = tk.Button(
            control_frame, 
            text=f"🚀 Vitesse: x{current_speed}", 
            font=("Helvetica", 12, "bold"),
            bg="#4682B4", 
            fg="white", 
            width=12,
            command=self.toggle_speed
        )
        self.btn_speed.pack(pady=5)

        # Bouton Pause
        self.btn_pause = tk.Button(
            control_frame, 
            text="⏸ Pause", 
            font=("Helvetica", 12, "bold"),
            bg="#FFA500", 
            fg="white", 
            width=12,
            command=self.toggle_pause
        )
        self.btn_pause.pack(pady=5)
        
        # Bouton Arrêter
        tk.Button(
            control_frame, 
            text="🛑 Arrêter", 
            font=("Helvetica", 12, "bold"),
            bg="#8B0000", 
            fg="white", 
            width=12,
            command=self.stop_game
        ).pack(pady=5)
        
        # Barre de navigation du bas
        nav_frame = tk.Frame(self, bg="#1e1e1e")
        nav_frame.pack(side="bottom", fill="x", padx=50, pady=20)
        
        tk.Button(
            nav_frame, 
            text="← Menu", 
            font=("Helvetica", 14, "bold"),
            fg="white", 
            bg="#3a3a3a", 
            width=15,
            command=self.return_to_menu
        ).pack(side="left")
        
        # Aide raccourcis
        tk.Label(
            nav_frame,
            text="[P]: Pause  [Espace]: Vitesse  [Echap]: Quitter",
            font=("Helvetica", 10), fg="gray", bg="#1e1e1e"
        ).pack(side="right")
    
    def tkraise(self, aboveThis=None):
        """
        Surchargée pour initialiser le jeu quand l'écran s'affiche.
        Active également les raccourcis clavier.
        """
        super().tkraise(aboveThis)
        
        self.focus_set() 
        self.bind_all('<p>', self.on_key_pause)
        self.bind_all('<space>', self.on_key_speed)
        self.bind_all('<Escape>', self.on_key_exit)
        
        if not self.game_running:
            self.after(100, self.initialize_game)
    
    # Gestionnaires d'événements clavier
    def on_key_pause(self, event): self.toggle_pause()
    def on_key_speed(self, event): self.toggle_speed()
    def on_key_exit(self, event): self.stop_game()

    def start_log_redirection(self):
        """Active la redirection de stdout vers le widget Text"""
        if self.redirector is None:
            self.redirector = RedirectText(self.log_text)
            sys.stdout = self.redirector

    def stop_log_redirection(self):
        """Désactive la redirection de stdout"""
        if self.redirector:
            sys.stdout = self.redirector.original_stdout
            self.redirector = None

    def initialize_game(self):
        """Récupère les paramètres, crée les entités et lance la boucle de jeu"""
        params = self.controller.parametres_partie
        
        # Reset logs
        self.log_text.delete(1.0, tk.END)
        self.start_log_redirection()
        print("--- Initialisation de la partie ---")
        
        # Préparation Carte
        self.map_jeu = self.convert_map(params.get("map_data", []))
        
        # Préparation Robots
        self.create_robots(params)
        
        # Préparation UI
        self.create_stats_widgets()
        self.draw_map()
        self.update_stats()
        
        # Démarrage Thread
        self.game_running = True
        self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.game_thread.start()
    
    def create_stats_widgets(self):
        """Génère les widgets de stats (barres de vie) pour chaque robot"""
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        self.robot_ui_elements = {}
        
        for robot in self.tous_les_robots:
            row = tk.Frame(self.stats_container, bg="#1e1e1e", pady=5)
            row.pack(fill="x")
            
            color = self.robot_colors.get(robot.Robotname, "white")
            
            lbl_name = tk.Label(
                row, text=robot.Robotname, 
                font=("Helvetica", 12, "bold"), 
                fg=color, bg="#1e1e1e", width=4, anchor="w"
            )
            lbl_name.pack(side="left")
            
            # Canvas barre de vie
            pb_canvas = tk.Canvas(
                row, width=150, height=20, 
                bg="#404040", highlightthickness=0
            )
            pb_canvas.pack(side="left", padx=10, fill="x", expand=True)
            
            # Rectangle de remplissage
            fill_rect = pb_canvas.create_rectangle(0, 0, 0, 20, fill="green", width=0)
            
            lbl_val = tk.Label(
                row, text=str(robot.energie), 
                font=("Courier", 10, "bold"), 
                fg="white", bg="#1e1e1e", width=6, anchor="e"
            )
            lbl_val.pack(side="right")
            
            self.robot_ui_elements[robot] = (pb_canvas, fill_rect, lbl_val, lbl_name)

    def convert_map(self, map_data):
        """Convertit la carte texte en carte numérique (0/1)"""
        result = []
        for row in map_data:
            int_row = []
            for char in row:
                if char == '#': int_row.append(1) # Obstacle
                else: int_row.append(0) # Libre
            result.append(int_row)
        return result
    
    def create_robots(self, params):
        """Instancie les robots et injecte les méthodes personnalisées"""
        energie = params.get("energie", 1500)
        distance = params.get("distance", 4)
        robot_files = params.get("robots_files", [])
        
        positions = self.find_start_positions(len(robot_files))
        
        self.tous_les_robots = []
        for i, (fichier, (x, y)) in enumerate(zip(robot_files, positions)):
            robot_name = f"R{i+1}"
            robot = Robot(
                x, y, energie, fichier,
                distance_reperage=distance,
                Robotname=robot_name,
                circuit_secours="AL",
                map_jeu = self.map_jeu
            )
            robot.charger_programme(fichier)
            robot.max_energie = energie 
            
            # Injection des tirs personnalisés (avec animation)
            robot.TH = lambda r=robot: self.custom_shot(r, "TH")
            robot.TV = lambda r=robot: self.custom_shot(r, "TV")
            
            self.tous_les_robots.append(robot)
            
            if 0 <= y < len(self.map_jeu) and 0 <= x < len(self.map_jeu[0]):
                self.map_jeu[y][x] = robot_name
    
    def custom_shot(self, robot, type_shot):
        """Gère le tir avec animation laser et effets visuels"""
        direction = ""
        dx, dy = 0, 0
        
        if type_shot == "TH":
            direction = random.choice(['G', 'D'])
            dx = -1 if direction == 'G' else 1
        else: # TV
            direction = random.choice(['H', 'B'])
            dy = -1 if direction == 'H' else 1
            
        x, y = robot.x + dx, robot.y + dy
        impact_found = False
        target_hit = None
        
        # Raycasting pour trouver l'impact
        while 0 <= x < 30 and 0 <= y < 20:
            cell = self.map_jeu[y][x]
            
            if cell == 1: # Mur
                impact_found = True
                break
            
            if cell != 0: # Mine ou Robot
                impact_found = True
                target_hit = cell
                
                if cell == "Mine":
                    is_own_mine = (y, x) in robot.mines_posees
                    if not is_own_mine:
                        self.map_jeu[y][x] = 0
                        print(f"💥 Tir de {robot.Robotname} détruit une mine en ({x}, {y})")
                        break
                else: # Robot
                    for target in self.tous_les_robots:
                        if target.Robotname == cell:
                            target.energie -= 20
                            print(f"🎯 {robot.Robotname} touche {target.Robotname} (-20 énergie)")
                            break
                    break
            x += dx
            y += dy
            
        robot.energie -= couts[type_shot]
        
        # Animation
        start_x, start_y = robot.x, robot.y
        end_x, end_y = x, y 
        if not impact_found:
            end_x -= dx
            end_y -= dy
            
        self.after(0, lambda: self.animate_laser(start_x, start_y, end_x, end_y, impact_found))

    def animate_laser(self, x1, y1, x2, y2, hit):
        """Dessine un laser temporaire sur le canvas"""
        px1 = x1 * self.cell_size + self.cell_size // 2
        py1 = y1 * self.cell_size + self.cell_size // 2
        px2 = x2 * self.cell_size + self.cell_size // 2
        py2 = y2 * self.cell_size + self.cell_size // 2
        
        laser_id = self.canvas.create_line(px1, py1, px2, py2, fill="#FFFF00", width=3, arrow=tk.LAST)
        
        impact_id = None
        if hit:
            impact_id = self.canvas.create_oval(
                px2-10, py2-10, px2+10, py2+10, 
                outline="#FF4500", width=2
            )
        
        def clear_laser():
            self.canvas.delete(laser_id)
            if impact_id: self.canvas.delete(impact_id)
            
        self.after(1000, clear_laser)

    def find_start_positions(self, num_robots):
        """Trouve des positions de départ valides (coins/bords)"""
        positions = []
        height = len(self.map_jeu)
        width = len(self.map_jeu[0]) if height > 0 else 0
        candidates = [
            (2, 2), (width-3, 2), (2, height-3), (width-3, height-3),
            (width//2, 2), (width//2, height-3), (2, height//2), (width-3, height//2)
        ]
        for x, y in candidates:
            if len(positions) >= num_robots: break
            if (0 <= y < height and 0 <= x < width and self.map_jeu[y][x] == 0):
                positions.append((x, y))
        return positions
    
    def game_loop(self):
        """Boucle principale du jeu (exécutée dans un thread)"""
        max_turns = 2000
        while self.game_running and self.current_turn < max_turns:
            if not self.game_paused:
                self.execute_turn()
                self.current_turn += 1
                
                # Mises à jour UI (via after pour thread-safety)
                self.after(0, self.draw_map)
                self.after(0, self.update_stats)
                self.after(0, lambda: self.lbl_turn.config(text=f"Tour: {self.current_turn}"))
                
                active_robots = [r for r in self.tous_les_robots if r.actif and r.energie > 0]
                if len(active_robots) <= 1:
                    self.after(0, lambda: self.show_winner(active_robots))
                    break
            
            # Gestion de la vitesse dynamique
            multiplier = self.speed_multipliers[self.current_speed_index]
            delay = self.base_delay / multiplier
            time.sleep(delay)
    
    def execute_turn(self):
        """Exécute un tour complet pour tous les robots"""
        for robot in self.tous_les_robots:
            if robot.actif and robot.energie > 0:
                robot.map_jeu = self.map_jeu
                robot.tous_les_robots = self.tous_les_robots
                robot.executer_pas()
        
        for robot in self.tous_les_robots:
            if robot.energie <= 0 and robot.actif:
                robot.actif = False
                print(f"⚰️ {robot.Robotname} est hors-jeu!")
    
    def draw_map(self):
        """Redessine entièrement la carte (Murs, Mines, Robots)"""
        self.canvas.delete("all")
        
        # Quadrillage
        for x in range(0, self.canvas_width + 1, self.cell_size):
            self.canvas.create_line(x, 0, x, self.canvas_height, fill="#505050")
        for y in range(0, self.canvas_height + 1, self.cell_size):
            self.canvas.create_line(0, y, self.canvas_width, y, fill="#505050")
        
        for y, row in enumerate(self.map_jeu):
            for x, cell in enumerate(row):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                if cell == 1:  # Obstacle (Noir)
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
                elif cell == "Mine":
                    # Mine colorée selon le propriétaire
                    mine_color = "#FF4500"
                    for robot in self.tous_les_robots:
                        if (y, x) in robot.mines_posees:
                            mine_color = self.robot_colors.get(robot.Robotname, "#FF4500")
                            break
                    self.canvas.create_oval(x1+5, y1+5, x2-5, y2-5, fill=mine_color, outline="white")
                    
                elif cell in self.robot_colors:  # Robot
                    robot = next((r for r in self.tous_les_robots if r.Robotname == cell), None)
                    if robot and not robot.invisible:
                        self.canvas.create_rectangle(
                            x1+2, y1+2, x2-2, y2-2,
                            fill=self.robot_colors[cell], outline="white", width=2
                        )
                        self.canvas.create_text((x1+x2)//2, (y1+y2)//2, text=cell, fill="white", font=("Helvetica", 10, "bold"))
    
    def update_stats(self):
        """Met à jour les valeurs et couleurs des barres de vie"""
        for robot, (pb_canvas, fill_rect, lbl_val, lbl_name) in self.robot_ui_elements.items():
            current_energy = max(0, robot.energie)
            canvas_width = pb_canvas.winfo_width()
            if canvas_width <= 1: canvas_width = 150
            
            ratio = current_energy / robot.max_energie if robot.max_energie > 0 else 0
            bar_width = int(canvas_width * ratio)
            
            pb_canvas.coords(fill_rect, 0, 0, bar_width, 20)
            lbl_val.config(text=str(current_energy))
            
            if current_energy < (robot.max_energie * 0.2):
                pb_canvas.itemconfig(fill_rect, fill="red")
            else:
                pb_canvas.itemconfig(fill_rect, fill="green")
            
            if not robot.actif or current_energy <= 0:
                lbl_name.config(fg="gray", font=("Helvetica", 12, "overstrike"))
                lbl_val.config(fg="gray")
            elif robot.invisible:
                lbl_name.config(text=f"{robot.Robotname} 👻")
            else:
                lbl_name.config(text=robot.Robotname, font=("Helvetica", 12, "bold"))

    def toggle_speed(self):
        """Change la vitesse de simulation"""
        self.current_speed_index = (self.current_speed_index + 1) % len(self.speed_multipliers)
        new_speed = self.speed_multipliers[self.current_speed_index]
        self.btn_speed.config(text=f"🚀 Vitesse: x{new_speed}")

    def toggle_pause(self):
        """Met en pause ou reprend le jeu"""
        self.game_paused = not self.game_paused
        self.btn_pause.config(text="▶ Reprendre" if self.game_paused else "⏸ Pause")
    
    def stop_game(self):
        """Arrête la partie avec confirmation"""
        was_paused = self.game_paused
        self.game_paused = True
        
        if messagebox.askyesno("Arrêter", "Voulez-vous vraiment arrêter la partie?"):
            self.return_to_menu()
        else:
            self.game_paused = was_paused
    
    def show_winner(self, active_robots):
        """Affiche le vainqueur"""
        if active_robots:
            winner = active_robots[0]
            messagebox.showinfo("Victoire!", f"🏆 {winner.Robotname} remporte la victoire!\n\nÉnergie restante: {winner.energie}")
        else:
            messagebox.showinfo("Match nul", "⚔️ Égalité! Tous les robots sont hors-jeu.")
        self.game_running = False
    
    def return_to_menu(self):
        """Nettoie et retourne au menu principal"""
        self.stop_log_redirection()
        self.unbind_all('<p>')
        self.unbind_all('<space>')
        self.unbind_all('<Escape>')
        
        self.game_running = False
        self.game_paused = False
        self.current_turn = 0
        self.tous_les_robots = []
        self.map_jeu = []
        self.controller.show_frame("Menu")