#!/usr/bin/env python3
"""
Génération à la demande d'un fichier MP3 pour une phrase spécifique.
Utilisé par l'API lorsque l'utilisateur clique sur le bouton de téléchargement.
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Import conditionnel de PyDub
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print(json.dumps({'success': False, 'error': 'PyDub non disponible'}))
    sys.exit(1)


def sanitize_keyword(keyword: str) -> str:
    """Nettoyer un mot-clé pour l'utiliser dans un nom de fichier."""
    # Prendre uniquement la partie avant ≈ si présent
    if '≈' in keyword:
        keyword = keyword.split('≈')[0].strip()
    
    # Remplacer les caractères spéciaux par des underscores
    sanitized = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in keyword)
    return sanitized


def generate_phrase_audio(phrase_data: dict, phrase_index: int) -> dict:
    """
    Génère un fichier MP3 pour une phrase spécifique.
    
    Args:
        phrase_data: Dictionnaire contenant les informations de la phrase
        phrase_index: Index de la phrase (pour le nom du fichier)
    
    Returns:
        dict: {'success': bool, 'audio_file': str, 'duration': float}
    """
    try:
        # Vérifier les données requises
        required_fields = ['start_time', 'end_time']
        for field in required_fields:
            if field not in phrase_data:
                return {'success': False, 'error': f'Champ manquant: {field}'}
        
        # Déterminer le chemin du fichier audio
        # Priorité: audio_path (chemin complet) > file_name (nom de fichier)
        if 'audio_path' in phrase_data and phrase_data['audio_path']:
            audio_file = Path(phrase_data['audio_path'])
        elif 'file_name' in phrase_data:
            # Construire le chemin depuis file_name
            project_root = Path(__file__).parent.parent
            file_name = phrase_data['file_name']
            
            # Si c'est un chemin absolu, l'utiliser directement
            if os.path.isabs(file_name):
                audio_file = Path(file_name)
            else:
                # Sinon, chercher dans le dossier audio
                audio_dir = project_root / 'audio'
                audio_file = None
                
                # Rechercher le fichier audio avec différentes extensions
                for ext in ['.wav', '.mp3', '.m4a', '']:
                    if ext == '':
                        # Essayer le nom tel quel (peut-être qu'il a déjà l'extension)
                        potential_path = audio_dir / file_name
                    else:
                        potential_path = audio_dir / f"{file_name}{ext}"
                    
                    if potential_path.exists():
                        audio_file = potential_path
                        break
        else:
            return {'success': False, 'error': 'Aucun chemin audio fourni (audio_path ou file_name manquant)'}
        
        if not audio_file or not audio_file.exists():
            return {'success': False, 'error': f"Fichier audio non trouvé: {phrase_data.get('audio_path') or phrase_data.get('file_name')}"}
        
        # Charger l'audio source
        source_audio = AudioSegment.from_file(str(audio_file))
        
        # Extraire la phrase avec padding
        # Utiliser extended_end_time si disponible (pour inclure les phrases suivantes +1, +2)
        start_ms = int(phrase_data['start_time'] * 1000)
        
        # Priorité à extended_end_time (qui inclut les extensions), sinon end_time
        if 'extended_end_time' in phrase_data and phrase_data['extended_end_time']:
            end_ms = int(phrase_data['extended_end_time'] * 1000)
        else:
            end_ms = int(phrase_data['end_time'] * 1000)
        
        padding_ms = 100
        start_ms = max(0, start_ms - padding_ms)
        end_ms = min(len(source_audio), end_ms + padding_ms)
        
        phrase_audio = source_audio[start_ms:end_ms]
        
        # Normaliser et ajouter des fades
        phrase_audio = phrase_audio.normalize()
        phrase_audio = phrase_audio.fade_in(100).fade_out(100)
        
        # Générer le nom du fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Déterminer le mot-clé principal
        keywords = phrase_data.get('keywords_found', [])
        if keywords:
            keyword = sanitize_keyword(keywords[0])
        else:
            keyword = 'extrait'
        
        filename = f"extrait_{keyword}_{phrase_index + 1}_{timestamp}.mp3"
        
        # Créer le dossier de destination
        output_dir = Path(__file__).parent / 'public' / 'audio'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        # Exporter en MP3
        phrase_audio.export(
            str(output_path),
            format='mp3',
            bitrate='192k',
            parameters=['-q:a', '2']
        )
        
        duration = len(phrase_audio) / 1000.0
        
        return {
            'success': True,
            'audio_file': filename,
            'duration': duration,
            'phrase_index': phrase_index
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({'success': False, 'error': 'Arguments manquants'}))
        sys.exit(1)
    
    try:
        # Récupérer les données de la phrase depuis les arguments
        phrase_data = json.loads(sys.argv[1])
        phrase_index = int(sys.argv[2])
        
        result = generate_phrase_audio(phrase_data, phrase_index)
        print(json.dumps(result))
        
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)
