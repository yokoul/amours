#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour extraire un segment audio basé sur les timecodes
Utilisé par l'interface de recherche pour télécharger les extraits
"""

import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print(json.dumps({
        'success': False,
        'error': 'PyDub non disponible'
    }))
    sys.exit(1)

def extract_audio_segment(audio_path: str, start_time: float, end_time: float, output_dir: str) -> dict:
    """
    Extrait un segment audio et le sauvegarde
    
    Args:
        audio_path: Chemin vers le fichier audio source
        start_time: Début en secondes
        end_time: Fin en secondes
        output_dir: Répertoire de sortie
        
    Returns:
        Dictionnaire avec les informations du fichier généré
    """
    try:
        # Charger l'audio source
        audio = AudioSegment.from_file(audio_path)
        
        # Convertir les secondes en millisecondes
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # Extraire le segment
        segment = audio[start_ms:end_ms]
        
        # Créer le nom du fichier
        source_name = Path(audio_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"search_{source_name}_{timestamp}.mp3"
        output_path = Path(output_dir) / output_filename
        
        # Créer le répertoire si nécessaire
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Exporter en MP3
        segment.export(
            str(output_path),
            format='mp3',
            bitrate='192k'
        )
        
        return {
            'success': True,
            'audio_file': output_filename,
            'duration': len(segment) / 1000.0,
            'size_bytes': output_path.stat().st_size
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Point d'entrée pour l'interface web"""
    if len(sys.argv) < 4:
        print(json.dumps({
            'success': False,
            'error': 'Usage: extract_audio_segment.py <audio_path> <start_time> <end_time>'
        }))
        sys.exit(1)
    
    audio_path = sys.argv[1]
    start_time = float(sys.argv[2])
    end_time = float(sys.argv[3])
    
    # Déterminer le répertoire de sortie
    script_dir = Path(__file__).parent
    output_dir = script_dir / "public" / "audio"
    
    # Extraire le segment
    result = extract_audio_segment(audio_path, start_time, end_time, str(output_dir))
    
    # Retourner le résultat en JSON
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
