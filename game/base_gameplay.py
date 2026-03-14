# window/base_gameplay.py
import tkinter as tk
from tkinter import messagebox

class BaseGameplay(tk.Frame):
    """Classe de base pour l'affichage du gameplay (local et online)"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")
        self.controller = controller
        
        # Game state
        self.current_turn = 0
        self.game_state = None
        
        # Visual parameters
        self.cell_size = 25
        self.canvas_width = 30 * self.cell_size
        self.canvas_height = 20 * self.cell_size
        
        # Couleurs des robots
        self.robot_colors = {
            "R1": "#FF0000",
            "R2": "#0000FF",
            "R3": "#00FF00",
            "R4": "#FFFF00",
            "R5": "#FF00FF",
            "R6": "#00FFFF",
            0: "#FF0000",
            1: "#0000FF",
            2: "#00FF00",
            3: "#FFFF00",
            4: "#FF00FF",
            5: "#00FFFF",
        }
        
        # UI elements (seront créés par setup_ui)
        self.canvas = None
        self.lbl_turn = None
        self.lbl_status = None
        self.stats_container = None
        self.log_text = None
        self.robot_ui_elements = {}
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Crée l'interface graphique commune"""
        # Title
        title_frame = tk.Frame(self, bg="#1e1e1e")
        title_frame.pack(pady=10)
        
        self.lbl_title = tk.Label(
            title_frame, 
            text="🤖 COMBAT EN COURS 🤖", 
            font=("Helvetica", 24, "bold"),
            fg="white", 
            bg="#1e1e1e"
        )
        self.lbl_title.pack()

        # Main content area
        content_frame = tk.Frame(self, bg="#1e1e1e")
        content_frame.pack(expand=True, fill="both", padx=20)
        
        # Left panel - Game canvas
        left_panel = tk.Frame(content_frame, bg="#1e1e1e")
        left_panel.pack(side="left", padx=10)
        
        self.canvas = tk.Canvas(
            left_panel, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg="#777777",
            highlightthickness=2, 
            highlightbackground="black",
            highlightcolor="black"
        )
        self.canvas.pack(pady=(0, 10))
        
        # Logs Area (optionnel, peut être caché pour online)
        self.log_frame = tk.Frame(left_panel, bg="#1e1e1e")
        self.log_frame.pack(fill="both", expand=True)
        
        tk.Label(
            self.log_frame, 
            text="📜 Journal de combat", 
            font=("Helvetica", 12, "bold"), 
            fg="#ffaa00", 
            bg="#1e1e1e", 
            anchor="w"
        ).pack(fill="x")
        
        self.log_text = tk.Text(
            self.log_frame, 
            height=8,
            bg="black", 
            fg="#00ff00", 
            font=("Consolas", 9),
            state="normal"
        )
        scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right panel - Robot stats and controls
        right_panel = tk.Frame(content_frame, bg="#1e1e1e", width=300)
        right_panel.pack(side="right", fill="y", padx=10)
        
        # Turn counter
        self.lbl_turn = tk.Label(
            right_panel, 
            text="Tour: 0", 
            font=("Helvetica", 16, "bold"),
            fg="yellow", 
            bg="#1e1e1e"
        )
        self.lbl_turn.pack(pady=10)
        
        # Status label (peut être utilisé différemment selon le mode)
        self.lbl_status = tk.Label(
            right_panel,
            text="",
            font=("Helvetica", 12),
            fg="green",
            bg="#1e1e1e"
        )
        self.lbl_status.pack(pady=5)
        
        # Robot stats area
        tk.Label(
            right_panel, 
            text="📊 État des Robots", 
            font=("Helvetica", 14, "bold"),
            fg="white", 
            bg="#1e1e1e"
        ).pack(pady=(5, 10))
        
        # Container pour les barres d'énergie
        self.stats_container = tk.Frame(right_panel, bg="#1e1e1e")
        self.stats_container.pack(pady=10, fill="x")
        
        # Control buttons frame (à remplir par les sous-classes)
        self.control_frame = tk.Frame(right_panel, bg="#1e1e1e")
        self.control_frame.pack(pady=20)
        
        # À implémenter dans les sous-classes
        self.setup_controls()
        
        # Bottom navigation
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

        # Keyboard shortcuts label
        self.lbl_shortcuts = tk.Label(
            nav_frame,
            text="",
            font=("Helvetica", 10), 
            fg="gray", 
            bg="#1e1e1e"
        )
        self.lbl_shortcuts.pack(side="right")
    
    def setup_controls(self):
        """À implémenter dans les sous-classes pour ajouter les boutons spécifiques"""
        pass
    
    def create_stats_widgets(self, robots):
        """Génère dynamiquement les barres de vie pour chaque robot"""
        # Nettoyer les anciens widgets
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        self.robot_ui_elements = {}
        
        for i, robot in enumerate(robots):
            row = tk.Frame(self.stats_container, bg="#1e1e1e", pady=5)
            row.pack(fill="x")
            
            # Récupérer le nom selon le format (Robot object ou dict)
            if hasattr(robot, 'Robotname'):
                name = robot.Robotname
                max_energie = getattr(robot, 'max_energie', robot.energie)
                robot_key = robot  # Pour les objets, on peut utiliser l'objet comme clé
            else:
                # Pour les dicts, utiliser l'index ou l'ID
                robot_id = robot.get('id', i)
                name = robot.get('name', f"R{robot_id}")
                max_energie = robot.get('max_energie', 1500)
                robot_key = robot_id  # Utiliser l'ID comme clé
            
            color = self.robot_colors.get(name, self.robot_colors.get(robot.get('id', i) if isinstance(robot, dict) else 0, "white"))
            
            lbl_name = tk.Label(
                row, text=name, 
                font=("Helvetica", 12, "bold"), 
                fg=color, bg="#1e1e1e", width=4, anchor="w"
            )
            lbl_name.pack(side="left")
            
            pb_canvas = tk.Canvas(
                row, 
                width=150, 
                height=20, 
                bg="#404040",
                highlightthickness=0
            )
            pb_canvas.pack(side="left", padx=10, fill="x", expand=True)
            
            fill_rect = pb_canvas.create_rectangle(0, 0, 0, 20, fill="green", width=0)
            
            energie = robot.energie if hasattr(robot, 'energie') else robot.get('energie', 0)
            lbl_val = tk.Label(
                row, 
                text=str(energie), 
                font=("Courier", 10, "bold"), 
                fg="white", bg="#1e1e1e", width=6, anchor="e"
            )
            lbl_val.pack(side="right")
            
            # Utiliser robot_key au lieu de robot directement
            self.robot_ui_elements[robot_key] = {
                'canvas': pb_canvas,
                'rect': fill_rect,
                'label': lbl_val,
                'name_label': lbl_name,
                'max_energie': max_energie
            }
    
    def draw_map(self, map_data=None, robots=None):
        """Dessine la carte et les robots"""
        self.canvas.delete("all")
        
        if map_data is None:
            return
        
        # Lignes de grille
        for x in range(0, self.canvas_width + 1, self.cell_size):
            self.canvas.create_line(x, 0, x, self.canvas_height, fill="#505050")
        
        for y in range(0, self.canvas_height + 1, self.cell_size):
            self.canvas.create_line(0, y, self.canvas_width, y, fill="#505050")

        # Dessiner la carte
        for y, row in enumerate(map_data):
            for x, cell in enumerate(row):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                if cell == 1 or cell == '#':  # Obstacle
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, 
                        fill="black", 
                        outline="black"
                    )
                elif cell == "Mine":
                    # Mines (avec couleur si possible)
                    mine_color = self.get_mine_color(x, y, robots)
                    self.canvas.create_oval(
                        x1+5, y1+5, x2-5, y2-5, 
                        fill=mine_color, 
                        outline="white"
                    )
        
        # Dessiner les robots
        if robots:
            self.draw_robots(robots)
    
    def get_mine_color(self, x, y, robots):
        """Détermine la couleur d'une mine selon son propriétaire"""
        if not robots:
            return "#FF4500"
        
        for robot in robots:
            if hasattr(robot, 'mines_posees'):
                if (y, x) in robot.mines_posees:
                    return self.robot_colors.get(robot.Robotname, "#FF4500")
        
        return "#FF4500"
    
    def draw_robots(self, robots):
        """Dessine les robots sur le canvas"""
        for robot in robots:
            # Supporter à la fois les objets Robot et les dicts
            if hasattr(robot, 'x'):  # Objet Robot
                x, y = robot.x, robot.y
                name = robot.Robotname
                active = robot.actif
                invisible = getattr(robot, 'invisible', False)
                energie = robot.energie
            else:  # Dict (mode online)
                x = robot.get('x', 0)
                y = robot.get('y', 0)
                name = robot.get('name', f"R{robot.get('id', 0)}")
                active = robot.get('active', False)
                invisible = robot.get('invisible', False)
                energie = robot.get('energie', 0)
            
            if not active or energie <= 0:
                continue
            
            if invisible:
                continue
            
            x1 = x * self.cell_size
            y1 = y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            
            color = self.robot_colors.get(name, self.robot_colors.get(robot.get('id') if isinstance(robot, dict) else 0, "white"))
            
            self.canvas.create_rectangle(
                x1+2, y1+2, x2-2, y2-2,
                fill=color,
                outline="white",
                width=2
            )
            
            self.canvas.create_text(
                (x1+x2)//2, (y1+y2)//2,
                text=name,
                fill="white",
                font=("Helvetica", 10, "bold")
            )
    
    def update_stats(self, robots=None):
        """Met à jour l'affichage des statistiques"""
        if robots is None:
            return
        
        for i, robot in enumerate(robots):
            # Trouver la clé correspondante
            if hasattr(robot, 'Robotname'):
                robot_key = robot
            else:
                robot_key = robot.get('id', i)
            
            if robot_key not in self.robot_ui_elements:
                continue
            
            elements = self.robot_ui_elements[robot_key]
            
            # Récupérer l'énergie selon le format
            if hasattr(robot, 'energie'):
                current_energy = max(0, robot.energie)
                active = robot.actif
                invisible = getattr(robot, 'invisible', False)
                name = robot.Robotname
            else:
                current_energy = max(0, robot.get('energie', 0))
                active = robot.get('active', False)
                invisible = robot.get('invisible', False)
                name = robot.get('name', f"R{robot.get('id', i)}")
            
            max_energie = elements['max_energie']
            canvas_width = elements['canvas'].winfo_width()
            if canvas_width <= 1:
                canvas_width = 150
            
            ratio = current_energy / max_energie if max_energie > 0 else 0
            bar_width = int(canvas_width * ratio)
            
            elements['canvas'].coords(elements['rect'], 0, 0, bar_width, 20)
            elements['label'].config(text=str(current_energy))
            
            # Couleur de la barre
            if current_energy < (max_energie * 0.2):
                elements['canvas'].itemconfig(elements['rect'], fill="red")
            else:
                elements['canvas'].itemconfig(elements['rect'], fill="green")
            
            # Statut du robot
            if not active or current_energy <= 0:
                elements['name_label'].config(fg="gray", font=("Helvetica", 12, "overstrike"))
                elements['label'].config(fg="gray")
            elif invisible:
                elements['name_label'].config(text=f"{name} 👻")
            else:
                elements['name_label'].config(text=name, font=("Helvetica", 12, "bold"))
    
    def return_to_menu(self):
        """Retour au menu - à implémenter dans les sous-classes"""
        self.controller.show_frame("Menu")