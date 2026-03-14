import socket
import json
import threading

class GameClient:
    """Client pour se connecter au serveur de jeu"""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.client_id = None
        self.callbacks = {
            'on_connect': None,
            'on_game_start': None,
            'on_turn_update': None,
            'on_game_end': None,
            'on_player_ready': None,
            'on_disconnect': None,
            'on_log': None  # 🔧 FIX: Ajouter on_log dans les callbacks par défaut
        }
        
    def connect(self, host, port):
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            print(f"✅ Connecté au serveur {host}:{port}")
            
            # Thread pour recevoir les messages
            receive_thread = threading.Thread(target=self.receive_loop)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
            
    def disconnect(self):
        """Se déconnecte du serveur"""
        if self.socket:
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
            if self.callbacks['on_disconnect']:
                self.callbacks['on_disconnect']()
                
    def receive_loop(self):
        """Boucle de réception des messages"""
        while self.connected:
            try:
                message = self.receive_message()
                if not message:
                    break
                    
                self.handle_message(message)
                
            except Exception as e:
                print(f"❌ Erreur réception: {e}")
                break
                
        self.disconnect()
        
    def handle_message(self, message):
        """Traite un message reçu du serveur"""
        msg_type = message.get('type')
        
        if msg_type == 'connection':
            self.client_id = message['client_id']
            print(f"🆔 ID reçu: {self.client_id}")
            if self.callbacks['on_connect']:
                self.callbacks['on_connect'](message)
                
        elif msg_type == 'game_start':
            print("🎮 La partie commence!")
            if self.callbacks['on_game_start']:
                self.callbacks['on_game_start'](message['state'])
                
        elif msg_type == 'turn_update':
            if self.callbacks['on_turn_update']:
                self.callbacks['on_turn_update'](message)
                
        elif msg_type == 'game_end':
            print("🏁 Fin de partie")
            if self.callbacks['on_game_end']:
                self.callbacks['on_game_end'](message)
                
        elif msg_type == 'player_ready':
            if self.callbacks['on_player_ready']:
                self.callbacks['on_player_ready'](message)

        elif msg_type == 'log':
            # 🔧 FIX: Gérer les logs
            if self.callbacks.get('on_log'):
                self.callbacks['on_log'](message)
            else:
                # Si pas de callback, afficher dans la console
                print(f"[SERVEUR] {message.get('text', '')}")
                
        elif msg_type == 'error':
            print(f"❌ Erreur serveur: {message['message']}")
            
    def send_robot_program(self, program, name):
        """Envoie le programme du robot au serveur"""
        self.send_message({
            'type': 'set_robot',
            'program': program,
            'name': name
        })
        
    def request_game_start(self):
        """Demande le démarrage de la partie"""
        self.send_message({'type': 'start_game'})
        
    def request_game_state(self):
        """Demande l'état actuel du jeu"""
        self.send_message({'type': 'get_state'})
        
    def send_message(self, message):
        """Envoie un message JSON au serveur"""
        if not self.connected:
            return False
            
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.sendall(len(data).to_bytes(4, 'big'))
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"❌ Erreur envoi: {e}")
            return False
            
    def receive_message(self):
        """Reçoit un message JSON du serveur"""
        # Recevoir la taille
        size_data = self.socket.recv(4)
        if not size_data:
            return None
        size = int.from_bytes(size_data, 'big')
        
        # Recevoir les données
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
            
        return json.loads(data.decode('utf-8'))
        
    def set_callback(self, event, callback):
        """Définit un callback pour un événement"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            print(f"⚠️ Callback inconnu: {event}")