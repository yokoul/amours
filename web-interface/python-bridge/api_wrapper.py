#!/usr/bin/env python3
"""
Pont API Python pour l'interface web spectacle d'amour
Wrapper autour de phrase_montage.py pour l'intégration Node.js
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Ajouter le répertoire parent au path pour importer les modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

def run_phrase_montage(word_count: int, keywords: List[str]) -> Dict[str, Any]:
    """
    Exécute phrase_montage.py avec les paramètres donnés
    
    Args:
        word_count: Nombre de phrases à générer
        keywords: Liste des mots-clés sélectionnés
        
    Returns:
        Dict avec le résultat de la génération
    """
    try:
        # Chemin vers le script phrase_montage.py
        script_path = parent_dir / "examples" / "phrase_montage.py"
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script phrase_montage.py non trouvé: {script_path}")
        
        # Utiliser l'environnement Python virtuel
        python_executable = parent_dir / ".venv" / "bin" / "python"
        
        if not python_executable.exists():
            # Fallback vers le Python système
            python_executable = sys.executable
        
        # Préparer les arguments
        args = [
            str(python_executable),  # Python executable depuis .venv
            str(script_path),
            str(word_count)
        ] + keywords
        
        print(f"🎭 Exécution: {' '.join(args)}", file=sys.stderr)
        
        # Exécuter le script
        result = subprocess.run(
            args,
            cwd=str(parent_dir),  # Répertoire de travail
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 60 secondes
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout.strip(),
                "stderr": result.stderr.strip() if result.stderr.strip() else None,
                "word_count": word_count,
                "keywords": keywords
            }
        else:
            return {
                "success": False,
                "error": f"Erreur d'exécution (code {result.returncode})",
                "output": result.stdout.strip() if result.stdout.strip() else None,
                "stderr": result.stderr.strip() if result.stderr.strip() else None,
                "word_count": word_count,
                "keywords": keywords
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout: La génération a pris trop de temps",
            "word_count": word_count,
            "keywords": keywords
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur inattendue: {str(e)}",
            "word_count": word_count,
            "keywords": keywords
        }

def get_vocabulary_words(count: int = 50) -> List[str]:
    """
    Récupère une liste de mots du vocabulaire d'amour
    
    Args:
        count: Nombre de mots à retourner
        
    Returns:
        Liste de mots
    """
    # Vocabulaire étendu d'amour en français
    love_vocabulary = [
        'passion', 'désir', 'tendresse', 'émotion', 'flamme',
        'cœur', 'âme', 'rêve', 'espoir', 'joie',
        'bonheur', 'extase', 'ivresse', 'folie', 'délire',
        'baiser', 'caresse', 'étreinte', 'regard', 'sourire',
        'larme', 'soupir', 'frisson', 'trouble', 'émoi',
        'séduction', 'charme', 'beauté', 'grâce', 'élégance',
        'étoile', 'lune', 'soleil', 'nuit', 'jour',
        'silence', 'murmure', 'chanson', 'mélodie', 'harmonie',
        'danse', 'valse', 'élan', 'envol', 'fuite',
        'mystère', 'secret', 'confidence', 'aveu', 'serment',
        'promesse', 'attente', 'présence', 'absence', 'nostalgie',
        'souvenir', 'mémoire', 'oubli', 'pardon', 'réconciliation',
        'fidélité', 'dévotion', 'adoration', 'vénération', 'culte',
        'communion', 'fusion', 'union', 'mariage', 'alliance',
        'renaissance', 'réveil', 'éveil', 'découverte', 'révélation',
        'miracle', 'prodige', 'enchantement', 'sortilège', 'magie',
        'paradis', 'eden', 'nirvana', 'béatitude', 'félicité',
        'langueur', 'mélancolie', 'spleen', 'cafard', 'blues',
        'passion', 'ardeur', 'ferveur', 'zèle', 'enthousiasme',
        'extase', 'transport', 'ravissement', 'émerveillement', 'stupéfaction'
    ]
    
    import random
    random.shuffle(love_vocabulary)
    return love_vocabulary[:count]

def main():
    """
    Point d'entrée principal pour l'API Python
    Peut être appelé depuis Node.js ou en ligne de commande
    """
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python api_wrapper.py <command> [args...]"
        }))
        return
    
    command = sys.argv[1]
    
    try:
        if command == "generate":
            if len(sys.argv) < 4:
                raise ValueError("Usage: python api_wrapper.py generate <word_count> <keyword1> [keyword2...]")
            
            word_count = int(sys.argv[2])
            keywords = sys.argv[3:]
            
            result = run_phrase_montage(word_count, keywords)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "vocabulary":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            words = get_vocabulary_words(count)
            
            result = {
                "success": True,
                "words": words,
                "count": len(words)
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "test":
            # Test simple
            result = run_phrase_montage(2, ["amour", "passion"])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        else:
            raise ValueError(f"Commande inconnue: {command}")
            
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()