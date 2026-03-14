"""
Module de validation des programmes de robots (.rbt).

Ce module fournit une fonction `valider_programme_robot` pour analyser
et vérifier la conformité des fichiers scripts utilisés par les robots dans le jeu.
Il s'assure que :
 Le fichier existe et est lisible.
 Le fichier n'est pas vide.
 Chaque instruction est syntaxiquement correcte et fait partie des commandes autorisées.
 Les paramètres des commandes sont valides.
"""

def valider_programme_robot(filepath):
    """
    Valide un fichier .rbt et retourne un tuple contenant le statut et les données.
    
    Args:
        filepath (str): Le chemin complet vers le fichier .rbt à analyser.

    Returns:
        tuple: (bool, list, str)
            - Le premier élément est un booléen : `True` si le programme est valide, `False` sinon.
            - Le deuxième élément est une liste de chaînes : le programme nettoyé (lignes valides sans espaces superflus) si valide, ou une liste vide `[]` sinon.
            - Le troisième élément est une chaîne : un message d'erreur explicite en cas d'échec, ou une chaîne vide `""` en cas de succès.
    """
    dirs = ["H", "B", "G", "D"]
    simple_instr = ["AL", "MI", "IN", "PS", "FT", "TH", "TV"]
    instr_tt = ["AL", "MI", "IN", "PS", "FT", "TH", "TV"]  # DD interdit dans TT
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lignes = f.readlines()
        
        programme = [ligne.strip() for ligne in lignes if ligne.strip()]
        
        if not programme:
            return False, [], "Le fichier est vide"
        
        for i, inst in enumerate(programme, 1):
            parts = inst.split()
            
            if not parts:
                continue
                
            # --- DD ---
            if parts[0] == "DD":
                if len(parts) == 2 and parts[1] in dirs:
                    continue
                else:
                    return False, [], f"Ligne {i}: DD invalide (format: DD H/B/G/D)"
            
            # --- TT ---
            elif parts[0] == "TT":
                if len(parts) == 3 and parts[1] in instr_tt and parts[2] in instr_tt:
                    continue
                else:
                    return False, [], f"Ligne {i}: TT invalide (format: TT instr1 instr2, DD interdit)"
            
            # --- Instructions simples ---
            elif parts[0] in simple_instr and len(parts) == 1:
                continue
            
            else:
                return False, [], f"Ligne {i}: Instruction inconnue ou mal formatée '{inst}'"
        
        return True, programme, ""
        
    except FileNotFoundError:
        return False, [], "Fichier introuvable"
    except Exception as e:
        return False, [], f"Erreur de lecture: {str(e)}"