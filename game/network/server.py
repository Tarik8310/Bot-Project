import socket
import threading
import random
import json
import time
import sys
import os

# ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robotdoc import Robot, largeur_grille, hauteur_grille

class GameServer:
    """Serveur multijoueur"""
    
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []  # liste des connexions clients
        self.client_robots = {}  # {client_id: robot_data}
        self.game_state = {
            'map': [],
            'robots': [],
            'turn': 0,
            'status': 'waiting'  # waiting, running, finished
        }
        self.max_players = 6
        self.game_params = {'energie': 1500, 'distance': 4}
        
        self.tous_les_robots = []
        self.map_jeu = []
        
    def start(self):
        """Démarre le serveur"""
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(self.max_players)
            
            # 🔧 FIX: Capturer le print AVANT de l'utiliser
            import builtins
            self.original_print = builtins.print

            def print_and_send(*args, **kwargs):
                text = " ".join(str(a) for a in args)
                self.original_print(text)
                # Ne broadcast que si une partie est en cours
                if self.game_state['status'] == 'running':
                    self.broadcast({'type': 'log', 'text': text})

            # Remplacer le print GLOBAL (pour robotdoc.py aussi)
            builtins.print = print_and_send
            
            print(f"🌐 Serveur démarré sur {self.host}:{self.port}")
            
            # Thread pour accepter les connexions
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {e}")
            sys.exit(1)
        
    def accept_connections(self):
        """Accepte les connexions des clients"""
        while True:
            try:
                client_socket, address = self.server.accept()
                print(f"✅ Nouvelle connexion: {address}")
                
                if len(self.clients) < self.max_players:
                    client_id = len(self.clients)
                    self.clients.append({
                        'socket': client_socket,
                        'address': address,
                        'id': client_id,
                        'ready': False
                    })
                    
                    # thread pour gerer ce client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_id)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # envoyer l'ID au client
                    self.send_message(client_socket, {
                        'type': 'connection',
                        'client_id': client_id,
                        'players_count': len(self.clients)
                    })
                else:
                    # serveur plein
                    self.send_message(client_socket, {
                        'type': 'error',
                        'message': 'Serveur complet'
                    })
                    client_socket.close()
                    
            except Exception as e:
                print(f"❌ Erreur acceptation: {e}")
                
    def handle_client(self, client_socket, client_id):
        """Gere les messages d'un client specifique"""
        while True:
            try:
                data = self.receive_message(client_socket)
                if not data:
                    break
                    
                self.process_message(client_id, data)
                
            except Exception as e:
                print(f"❌ Erreur client {client_id}: {e}")
                break
        
        # deconnexion
        self.remove_client(client_id)

    def send_log(self, msg):
        self.broadcast({
            'type': 'log',
            'text': msg
        })
        
    def process_message(self, client_id, message):
        """Traite un message reçu d'un client"""
        msg_type = message.get('type')
        
        print(f"📨 Message reçu de client {client_id}: {msg_type}")
        
        if msg_type == 'set_robot':
            # client envoie son programme robot
            self.client_robots[client_id] = {
                'program': message['program'],
                'name': message.get('name', f'Robot{client_id}')
            }
            
            # trouver le bon client dans la liste
            for client in self.clients:
                if client['id'] == client_id:
                    client['ready'] = True
                    break
            
            ready_count = sum(1 for c in self.clients if c.get('ready', False))
            print(f"✅ {self.client_robots[client_id]['name']} est prêt! ({ready_count}/{len(self.clients)})")
            
            self.broadcast({
                'type': 'player_ready',
                'client_id': client_id,
                'ready_count': ready_count
            })
            
            # launch auto si tous prets
            if self.all_ready():
                print("🎮 Tous les joueurs sont prêts! Démarrage dans 5 seconde...")
                threading.Timer(5.0, self.initialize_game).start()
                
        elif msg_type == 'start_game':
            if self.all_ready():
                self.initialize_game()
                
        elif msg_type == 'get_state':
            self.send_message(
                self.clients[client_id]['socket'],
                {'type': 'game_state', 'state': self.game_state}
            )
            
    def all_ready(self):
        """Vérifie si tous les joueurs sont prêts"""
        if len(self.clients) < 2:
            return False
        
        ready = all(c.get('ready', False) for c in self.clients)
        print(f"🔍 Vérification: {len(self.clients)} clients, tous prêts: {ready}")
        return ready
        
    def initialize_game(self):
        """Initialise la partie"""
        print("🎮 Initialisation de la partie...")
        
        # 🔧 FIX: Créer la map et la sauvegarder dans game_state
        raw_map = self.generate_map()
        self.game_state['map'] = raw_map  # Sauvegarder la map STRING
        
        # Convertir pour les robots (format int)
        self.map_jeu = self.convert_map_to_int(raw_map)
        
        print(f"🗺️  Map générée: {len(raw_map)} lignes, {len(raw_map[0]) if raw_map else 0} colonnes")
        print(f"   Première ligne: {raw_map[0] if raw_map else 'vide'}")
        
        # Créer les robots
        positions = self.find_start_positions(len(self.clients))
        robots_data = []
        self.tous_les_robots = []
        
        for i, client in enumerate(self.clients):
            robot_info = self.client_robots.get(i, {})
            x, y = positions[i]
            
            # Créer robot réel pour simulation
            robot = Robot(
                x, y,
                energie=self.game_params.get('energie', 1500),
                fichier="",
                distance_reperage=self.game_params.get('distance', 4),
                Robotname=f"R{i}",
                circuit_secours="AL",
                map_jeu=self.map_jeu
            )
            robot.programme = robot_info.get('program', ['AL'])
            robot.tous_les_robots = self.tous_les_robots
            self.tous_les_robots.append(robot)
            
            # État pour clients
            robots_data.append({
                'id': i,
                'name': robot_info.get('name', f'R{i}'),
                'x': x,
                'y': y,
                'energie': robot.energie,
                'program': robot.programme,
                'active': True
            })
        
        self.game_state['robots'] = robots_data
        self.game_state['status'] = 'running'
        
        # 🔧 DEBUG: Vérifier que la map est bien dans game_state
        print(f"🔍 DEBUG game_state['map'] contient {len(self.game_state['map'])} lignes")
        
        # Notifier tous les clients
        self.broadcast({
            'type': 'game_start',
            'state': self.game_state
        })
        
        print(f"🚀 Partie lancée avec {len(self.tous_les_robots)} robots!")
        
        # Démarrer la boucle de jeu
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = True
        game_thread.start()
        
    def game_loop(self):
        """Boucle principale du jeu sur le serveur"""
        max_turns = 2000
        
        while self.game_state['turn'] < max_turns and self.game_state['status'] == 'running':
            # Exécuter un tour
            self.execute_turn()
            self.game_state['turn'] += 1
            
            # Mettre à jour l'état des robots
            self.update_robots_state()
            
            # 🔧 FIX: S'assurer que la map est TOUJOURS envoyée
            if not self.game_state.get('map'):
                print("⚠️ WARNING: game_state['map'] est vide! Reconstruction...")
                self.game_state['map'] = self.convert_int_map_to_string(self.map_jeu)
            
            # Envoyer l'état à tous les clients
            self.broadcast({
                'type': 'turn_update',
                'turn': self.game_state['turn'],
                'robots': self.game_state['robots'],
                'map': self.game_state['map']
            })
            
            # Vérifier condition de victoire
            active = [r for r in self.tous_les_robots if r.actif and r.energie > 0]
            if len(active) <= 1:
                winner_robot = active[0] if active else None
                winner_data = None
                
                if winner_robot:
                    for robot_data in self.game_state['robots']:
                        if robot_data['name'] == winner_robot.Robotname or robot_data['id'] == self.tous_les_robots.index(winner_robot):
                            winner_data = robot_data
                            break
                
                print(f"🏆 Fin de partie! Vainqueur: {winner_robot.Robotname if winner_robot else 'Aucun'}")
                
                self.broadcast({
                    'type': 'game_end',
                    'winner': winner_data,
                    'turn': self.game_state['turn']
                })
                self.game_state['status'] = 'finished'
                break
            
            time.sleep(0.05)
            
        print("✅ Partie terminée")
            
    def execute_turn(self):
        """Exécute un tour de jeu avec les vrais robots"""
        for robot in self.tous_les_robots:
            if robot.actif and robot.energie > 0:
                robot.map_jeu = self.map_jeu
                robot.tous_les_robots = self.tous_les_robots
                robot.executer_pas()
        
        for robot in self.tous_les_robots:
            if robot.energie <= 0 and robot.actif:
                robot.actif = False
                print(f"💀 {robot.Robotname} est hors-jeu!")
    
    def update_robots_state(self):
        """Met à jour l'état des robots dans game_state"""
        for i, robot in enumerate(self.tous_les_robots):
            if i < len(self.game_state['robots']):
                self.game_state['robots'][i].update({
                    'x': robot.x,
                    'y': robot.y,
                    'energie': robot.energie,
                    'active': robot.actif,
                    'invisible': robot.invisible,
                    'mines': robot.mines_posees
                })
        
    def convert_map_to_int(self, map_data):
        """Convertit la map string en format int pour les robots"""
        result = []
        for row in map_data:
            int_row = []
            for char in row:
                if char == '#':
                    int_row.append(1)
                else:
                    int_row.append(0)
            result.append(int_row)
        return result
    
    def convert_int_map_to_string(self, int_map):
        """🔧 FIX: Convertit la map int en format string pour l'envoi"""
        result = []
        for row in int_map:
            string_row = ""
            for cell in row:
                if cell == 1 or cell == '#':
                    string_row += "#"
                elif cell == 'Mine' or cell == 'M':
                    string_row += "M"
                else:
                    string_row += "_"
            result.append(string_row)
        return result
        
    def generate_map(self):
        """Génère une grille 30x20 avec des obstacles aléatoires"""
        width = 30
        height = 20
        density = random.randrange(21) / 100.0
        map_data = [] 
        for y in range(height):
            row = ""
            for x in range(width):
                if x == 0 or x == width-1 or y == 0 or y == height-1:
                    row += "#"
                else:
                    if random.random() < density:
                        row += "#"
                    else:
                        row += "_"
            map_data.append(row)
        return self.corriger_diagonales_avec_densite(map_data)

    def corriger_diagonales_avec_densite(self, map_data, width=30, height=20):
        """Supprime les patterns diagonaux et compense en ajoutant des obstacles ailleurs"""
        modifie = True
        obstacles_supprimes = 0
        
        while modifie:
            modifie = False
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    if (map_data[y][x] == '#' and 
                        map_data[y][x+1] == '_' and
                        map_data[y+1][x] == '_' and 
                        map_data[y+1][x+1] == '#'):
                        if random.random() < 0.5:
                            map_data[y] = map_data[y][:x] + '_' + map_data[y][x+1:]
                        else:
                            map_data[y+1] = map_data[y+1][:x+1] + '_' + map_data[y+1][x+2:]
                        obstacles_supprimes += 1
                        modifie = True
                    
                    elif (map_data[y][x] == '_' and 
                        map_data[y][x+1] == '#' and
                        map_data[y+1][x] == '#' and 
                        map_data[y+1][x+1] == '_'):
                        if random.random() < 0.5:
                            map_data[y] = map_data[y][:x+1] + '_' + map_data[y][x+2:]
                        else:
                            map_data[y+1] = map_data[y+1][:x] + '_' + map_data[y+1][x+1:]
                        obstacles_supprimes += 1
                        modifie = True
        
        return self.ajouter_obstacles_safe(map_data, obstacles_supprimes)

    def ajouter_obstacles_safe(self, map_data, nombre):
        ajoutes = 0
        tentatives = 0
        max_tentatives = nombre * 100
        while ajoutes < nombre and tentatives < max_tentatives:
            tentatives += 1
            x = random.randint(1, 30 - 2)
            y = random.randint(1, 20 - 2)
            if map_data[y][x] == '_':
                if self.peut_ajouter_obstacle(x, y, map_data):
                    map_data[y] = map_data[y][:x] + '#' + map_data[y][x+1:]
                    ajoutes += 1
        return map_data

    def peut_ajouter_obstacle(self, x, y, map_data, width=30, height=20):
        if (x < width - 2 and y < height - 2 and map_data[y][x+1] == '_' and map_data[y+1][x] == '_' and map_data[y+1][x+1] == '#'): return False
        if (x > 0 and y < height - 2 and map_data[y][x-1] == '_' and map_data[y+1][x-1] == '#' and map_data[y+1][x] == '_'): return False
        if (x < width - 2 and y > 0 and map_data[y-1][x] == '_' and map_data[y-1][x+1] == '#' and map_data[y][x+1] == '_'): return False
        if (x > 0 and y > 0 and map_data[y-1][x-1] == '#' and map_data[y-1][x] == '_' and map_data[y][x-1] == '_'): return False
        return True

    def find_start_positions(self, num_robots):
        """Trouve des positions de départ"""
        positions = [(2, 2), (27, 2), (2, 17), (27, 17), (15, 2), (15, 17)]
        return positions[:num_robots]
        
    def broadcast(self, message):
        """Envoie un message à tous les clients"""
        for client in self.clients:
            try:
                self.send_message(client['socket'], message)
            except:
                pass
                
    def send_message(self, sock, message):
        """Envoie un message JSON à un socket"""
        try:
            data = json.dumps(message).encode('utf-8')
            sock.sendall(len(data).to_bytes(4, 'big'))
            sock.sendall(data)
        except Exception as e:
            print(f"❌ Erreur envoi message: {e}")
        
    def receive_message(self, sock):
        """Reçoit un message JSON d'un socket"""
        try:
            size_data = sock.recv(4)
            if not size_data:
                return None
            size = int.from_bytes(size_data, 'big')
            
            data = b''
            while len(data) < size:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
                
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"❌ Erreur réception message: {e}")
            return None
        
    def remove_client(self, client_id):
        """Retire un client déconnecté proprement"""
        print(f"❌ Client {client_id} déconnecté")

        self.clients = [c for c in self.clients if c['id'] != client_id]
        self.client_robots.pop(client_id, None)

        if self.game_state['status'] == 'waiting':
            for new_id, client in enumerate(self.clients):
                old_id = client['id']
                client['id'] = new_id
                
                if old_id in self.client_robots:
                    self.client_robots[new_id] = self.client_robots.pop(old_id)

            self.broadcast({
                'type': 'players_update',
                'players_count': len(self.clients)
            })
        else:
            if client_id < len(self.tous_les_robots):
                self.tous_les_robots[client_id].actif = False

            for robot in self.game_state['robots']:
                if robot['id'] == client_id:
                    robot['active'] = False

            self.broadcast({
                'type': 'player_disconnected',
                'client_id': client_id
            })

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 SERVEUR DE JEU - ROBOTS WARS 🤖")
    print("=" * 50)
    
    server = GameServer()
    server.start()
    
    print("\n✅ Serveur en attente de joueurs...")
    print("📡 Les joueurs peuvent se connecter sur localhost:5555")
    print("⌨️  Appuyez sur Ctrl+C pour arrêter\n")
    
    try:
        while True:
            time.sleep(1)
            if server.game_state['status'] == 'finished':
                server.clients = []
                server.client_robots = {}
                server.game_state = {
                    'map': [],
                    'robots': [],
                    'turn': 0,
                    'status': 'waiting'
                }
                print("Partie Terminée, RESET SERVEUR")

    except KeyboardInterrupt:
        print("\n\n👋 Arrêt du serveur...")
        print("Merci d'avoir joué! 🎮")