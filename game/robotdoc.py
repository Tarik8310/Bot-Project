from random import randrange, choice
import math
# Coûts énergétiques des actions
couts = {
            'DD': 5,
            'AL': 1,
            'PS': 4,
            'FT': 4,
            'MI': 10,
            'TH': 3,
            'TV': 3,
            'IN': 20,
            'TT': 4
        }

largeur_grille=30
hauteur_grille=20


class Robot:
    """
    Classe représentant un robot de combat dans le jeu de la guerre des robots.
    """
    def __init__(self, x, y, energie, fichier, distance_reperage=4, Robotname="default", circuit_secours="AL",map_jeu=[]):
        """
        Initialise un robot.
        
        Args:
            x (int): Position X initiale (0-29)
            y (int): Position Y initiale (0-19)
            energie (int): Énergie initiale (500-3000)
            programme (list): Liste d'instructions du programme
            distance_reperage (int): Distance de repérage (2-6, défaut 4)
            Robotname
        """
        self.x = x 
        self.y = y 
        self.energie = energie
        self.distance_reperage = distance_reperage
        self.Robotname = Robotname
        self.fichier_programme = fichier
        self.programme = []
        self.invisible = False
        self.mines_posees = []  # Liste des positions de mines posées par ce robot
        self.actif = True
        self.pas_courant = 0
        self.circuit_secours = circuit_secours
        self.map_jeu=map_jeu
    
        if self.map_jeu and 0 <= y < len(self.map_jeu) and 0 <= x < len(self.map_jeu[0]):
            if self.map_jeu[y][x] == 0:
                self.map_jeu[y][x] = self.Robotname

    def charger_programme(self, fichier):
        """
        Charge un programme depuis un fichier .rbt
        
        Args:
            fichier (str): Chemin du fichier programme
        """
        try:
            with open(fichier, 'r') as f:
                lignes = f.readlines()       
            self.programme = [ligne.strip() for ligne in lignes if ligne.strip()]
            self.pas_courant = 0
            print(f"Programme chargé pour {self.Robotname}: {self.programme}")
        except FileNotFoundError:
            print(f"⚠️ Fichier {fichier} introuvable. Programme vide.")
            self.programme = []
        #il va falloir check si les parametres d'instructions sont ok

    def executer_instruction(self, instruction):

        """
        Exécute une seule instruction
        """
        if not self.actif or self.energie <= 0:
            return
        
        # Gestion de l'instruction TT (test)
        if instruction.startswith("TT"):
            parts = instruction.split()
            if len(parts) >= 3:
                # TT instruction_si_proche instruction_si_loin
                if self.robot_proche_detecte():
                    self.executer_instruction(parts[1])
                else:
                    self.executer_instruction(parts[2])
                self.energie -= couts['TT']
            return
        
        # Instructions simples
        code = instruction[:2]
        
        if code == "DD":
            if len(instruction) >= 3:
                direction = instruction[2:].strip()
                self.DD(direction)
        elif code == "AL":
            self.AL()
        elif code == "IN":
            self.IN()
        elif code == "MI":
            self.MI()
        elif code == "PS":
            self.PS()
        elif code == "FT":
            self.FT()
        elif code == "TH":
            self.TH()
        elif code == "TV":
            self.TV()

    def executer_pas(self):
        """
        Exécute le pas courant du programme et passe au suivant
        """
        if not self.actif or self.energie <= 0 or not self.programme:
            self.actif = False
            return
        
        instruction = self.programme[self.pas_courant]
        self.executer_instruction(instruction)
        
        # Passer au pas suivant (boucle sur le programme)
        self.pas_courant = (self.pas_courant + 1) % len(self.programme)

    def robot_proche_detecte(self):
        """
        Détecte si un robot adverse est à portée de repérage
        """
        for robot in self.tous_les_robots:
            if robot != self and robot.actif and not robot.invisible:
                distance = self.calculer_distance(robot.x, robot.y)
                if distance <= self.distance_reperage:
                    return True
        return False
    
    def trouver_robot_plus_proche(self):
        """
        Trouve le robot adverse le plus proche (non invisible)
        Retourne (robot, distance) ou (None, None)
        """
        plus_proche = None
        dist_min = float('inf')
        
        for robot in self.tous_les_robots:
            if robot != self and robot.actif and robot.invisible == False:
                distance = self.calculer_distance(robot.x, robot.y)
                if distance < dist_min:
                    dist_min = distance
                    plus_proche = robot
        
        return plus_proche, dist_min if plus_proche else None

    def calculer_distance(self, x, y):
        """
        Calcule la distance euclidienne vers une position
        """
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    def deplacer_vers(self, tx, ty):
        """
        Déplace le robot d'une case vers la cible (tx, ty)
        Peut se déplacer en diagonale
        """
        self.map_jeu[self.y][self.x] = 0
        
        # Déterminer la direction
        dx = 0 if tx == self.x else (1 if tx > self.x else -1)
        dy = 0 if ty == self.y else (1 if ty > self.y else -1)
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        if self.map_jeu[new_y][new_x] == 0 or self.map_jeu[new_y][new_x] == "Mine":
            if self.map_jeu[new_y][new_x] == "Mine":
                self.marcher_sur_mine(new_x, new_y)
            self.x, self.y = new_x, new_y
        # Remettre le robot sur la carte
        self.map_jeu[self.y][self.x] = self.Robotname

    def marcher_sur_mine(self, x, y):
        """
        Gère l'explosion d'une mine
        """
        # Vérifier si c'est une de nos mines
        if (y, x) not in self.mines_posees:
            print(f"💥 {self.Robotname} a marché sur une mine!")
            self.energie -= 200
            
            # Remplacer l'instruction actuelle par le circuit de secours
            if self.programme:
                self.programme[self.pas_courant] = self.circuit_secours
                print(f"⚙️ Pas {self.pas_courant} remplacé par {self.circuit_secours}")
        else:
            print(f"{self.Robotname} est passé sur sa propre mine")
        
        # Détruire la mine dans tous les cas
        self.map_jeu[y][x] = 0
        # Retirer de la liste des mines posées
        if (y, x) in self.mines_posees:
            self.mines_posees.remove((y, x))

    

#DD : déplacement déterministe d’une case dans une direction fournie (H : haut, B : bas, D : droite, G : gauche)
# si la case visée est libre sinon reste sur place. C’est une instruction importante pour les terrains dégagés.
    def DD(self,direction):
        self.map_jeu[self.y][self.x] = 0
        
        # Calcul du déplacement
        new_x, new_y = self.x, self.y

        if direction == "H" and self.y > 0:
            new_y -= 1
        elif direction == "B" and self.y < hauteur_grille - 1:
            new_y += 1
        elif direction == "D" and self.x < largeur_grille - 1:
            new_x += 1
        elif direction == "G" and self.x > 0:
            new_x -= 1


        if self.map_jeu[new_y][new_x] == 0 or self.map_jeu[new_y][new_x] == "Mine":
            if self.map_jeu[new_y][new_x] == "Mine":
                self.marcher_sur_mine(new_x, new_y)
            self.x, self.y = new_x, new_y

        if self.map_jeu[new_y][new_x] == 0:
            self.x, self.y = new_x, new_y
        
        # Remettre le robot sur la carte
        self.map_jeu[self.y][self.x] = self.Robotname

        # Consommer de l’énergie
        self.energie -= couts['DD']


    def AL(self):
        """Déplacement aléatoire"""
        direction = choice(["H", "B", "G", "D"])
        self.DD(direction)
        self.energie += couts['DD'] - couts['AL']  # Ajuster le coût

    def IN(self):
        """Invisibilité"""
        if not self.invisible:
            self.invisible = True
            self.energie -= couts['IN']
            print(f"🔮 {self.Robotname} devient invisible")
        else:
            self.invisible = False
            print(f"👁️ {self.Robotname} redevient visible")

    def MI(self):
        """Pose d'une mine"""
        directions = [
            (-1, 0),  # Haut
            (1, 0),   # Bas
            (0, -1),  # Gauche
            (0, 1)    # Droite
        ]
        
        # Mélanger les directions pour essayer au hasard
        from random import shuffle
        shuffle(directions)
        
        for dy, dx in directions:
            ny, nx = self.y + dy, self.x + dx
            if (0 <= ny < hauteur_grille and 
                0 <= nx < largeur_grille and 
                self.map_jeu[ny][nx] == 0):
                
                self.map_jeu[ny][nx] = "Mine"
                self.mines_posees.append((ny, nx))
                self.energie -= couts['MI']
                print(f"💣 {self.Robotname} pose une mine en ({nx}, {ny})")
                return
        
        print(f"⚠️ {self.Robotname} ne peut pas poser de mine (aucune case libre)")


    def PS(self):
        """Poursuite du robot le plus proche"""
        robot_cible, distance = self.trouver_robot_plus_proche()
        
        if robot_cible:
            self.deplacer_vers(robot_cible.x, robot_cible.y)
            self.energie -= couts['PS']
        else:
            print(f"{self.Robotname}: Aucun robot à poursuivre")

    def FT(self):
        """Fuite du robot le plus proche"""
        robot_cible, distance = self.trouver_robot_plus_proche()
        
        if robot_cible:
            # Fuir dans la direction opposée
            dx = self.x - robot_cible.x
            dy = self.y - robot_cible.y
            
            # Normaliser la direction
            if dx != 0:
                dx = dx // abs(dx)
            if dy != 0:
                dy = dy // abs(dy)
            
            tx = self.x + dx
            ty = self.y + dy
            
            self.deplacer_vers(tx, ty)
            self.energie -= couts['FT']
        else:
            print(f"{self.Robotname}: Aucun robot à fuir")
    

    def TH(self):
        """Tir horizontal"""
        direction = choice(['G', 'D'])
        dx = -1 if direction == 'G' else 1
        
        x = self.x + dx
        while 0 <= x < largeur_grille:
            cible = self.map_jeu[self.y][x]
            
            if cible == "Mine":
                # Détruire la mine si ce n'est pas la nôtre
                if (self.y, x) not in self.mines_posees:
                    self.map_jeu[self.y][x] = 0
                    print(f"💥 Tir de {self.Robotname} détruit une mine en ({x}, {self.y})")
                    break
            elif cible != 0:
                # Robot touché
                for robot in self.tous_les_robots:
                    if robot.Robotname == cible:
                        robot.energie -= 20
                        print(f"🎯 {self.Robotname} touche {robot.Robotname} (-20 énergie)")
                        break
                break
            
            x += dx
        
        self.energie -= couts['TH']

    def TV(self):
        """Tir vertical"""
        direction = choice(['H', 'B'])
        dy = -1 if direction == 'H' else 1
        
        y = self.y + dy
        while 0 <= y < hauteur_grille:
            cible = self.map_jeu[y][self.x]
            
            if cible == "Mine":
                if (y, self.x) not in self.mines_posees:
                    self.map_jeu[y][self.x] = 0
                    print(f"💥 Tir de {self.Robotname} détruit une mine en ({self.x}, {y})")
                    break
            elif cible != 0:
                for robot in self.tous_les_robots:
                    if robot.Robotname == cible:
                        robot.energie -= 20
                        print(f"🎯 {self.Robotname} touche {robot.Robotname} (-20 énergie)")
                        break
                break
            
            y += dy
        
        self.energie -= couts['TV']







