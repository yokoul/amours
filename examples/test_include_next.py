#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du paramètre include_next_phrases
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from phrase_montage import PhraseSelector

def test_include_next():
    """Test avec et sans inclusion des phrases suivantes"""
    
    print("🧪 TEST INCLUDE_NEXT_PHRASES")
    print("=" * 60)
    
    # Initialiser
    selector = PhraseSelector()
    selector.load_phrases()
    
    # Rechercher des phrases
    keywords = ["amour", "bonheur"]
    matches = selector.search_phrases(keywords, max_results=3)
    
    if not matches:
        print("❌ Aucune phrase trouvée")
        return
    
    print(f"\n✅ {len(matches)} phrases trouvées\n")
    
    # Test 1: Sans extension (normal)
    print("=" * 60)
    print("TEST 1: MODE NORMAL (sans extension)")
    print("=" * 60)
    
    audio_normal = selector.generate_phrase_montage(
        matches,
        "output_mix_play/test_normal.mp3",
        include_next_phrases=0
    )
    print(f"✅ Fichier généré: {audio_normal}\n")
    
    # Test 2: Avec 1 phrase suivante
    print("=" * 60)
    print("TEST 2: MODE ÉTENDU (+1 phrase suivante)")
    print("=" * 60)
    
    audio_extended = selector.generate_phrase_montage(
        matches,
        "output_mix_play/test_extended_1.mp3",
        include_next_phrases=1
    )
    print(f"✅ Fichier généré: {audio_extended}\n")
    
    # Test 3: Avec 2 phrases suivantes
    print("=" * 60)
    print("TEST 3: MODE TRÈS ÉTENDU (+2 phrases suivantes)")
    print("=" * 60)
    
    audio_very_extended = selector.generate_phrase_montage(
        matches,
        "output_mix_play/test_extended_2.mp3",
        include_next_phrases=2
    )
    print(f"✅ Fichier généré: {audio_very_extended}\n")
    
    print("=" * 60)
    print("✅ Tests terminés !")
    print("\n💡 Écoutez les fichiers pour comparer:")
    print("   • test_normal.mp3 : phrases courtes")
    print("   • test_extended_1.mp3 : +1 phrase du même intervenant")
    print("   • test_extended_2.mp3 : +2 phrases du même intervenant")

if __name__ == "__main__":
    test_include_next()
