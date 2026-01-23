#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct d'une phrase depuis la ligne de commande
Usage: python test_phrase.py "ta phrase ici"
"""

import sys
from pathlib import Path
import re
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mix_player import MixPlayer

def test_phrase(phrase: str, show_details: bool = True):
    """Teste une phrase directement"""
    
    if show_details:
        print(f"🎯 Test de: {phrase}")
        print("-" * 50)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Nettoyer et composer
    words = re.findall(r'\b\w+\b', phrase.lower())
    
    composed = mix_player.compose_sentence(
        words,
        prioritize_diversity=True,
        min_confidence=0.3
    )
    
    if not composed.words:
        print("❌ Aucun mot trouvé dans cette phrase")
        return None
    
    # Générer l'audio
    timestamp = datetime.now().strftime("%H%M%S")
    output_dir = Path("output_mix_play")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"test_{timestamp}.mp3"
    
    try:
        audio_file = mix_player.generate_mixed_audio(
            composed,
            str(output_dir / filename),
            fade_mode="artistic",
            word_padding=0.1,
            tempo_factor=0.9,
        )
        
        print(f"✅ Audio généré: {filename}")
        
        # Lecture automatique sur macOS
        import platform
        if platform.system() == "Darwin":
            try:
                import subprocess
                subprocess.run(["afplay", audio_file], check=True)
                print("🎵 Lecture terminée")
            except:
                print(f"📂 Fichier: {audio_file}")
        
        return audio_file
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_phrase.py \"votre phrase ici\"")
        print("\nExemples:")
        print("  python test_phrase.py \"bonjour comment allez vous\"")
        print("  python test_phrase.py \"avec tout mon amour je te dis bonjour\"")
        sys.exit(1)
    
    phrase = " ".join(sys.argv[1:])
    test_phrase(phrase)