#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorateur de vocabulaire pour le système Mix-Play
Permet de voir quels mots sont disponibles dans les transcriptions
"""

import sys
sys.path.append('..')

from src.mix_player import MixPlayer
import difflib
from pathlib import Path

def explore_vocabulary():
    """Explore le vocabulaire disponible dans les transcriptions"""
    
    print("🔍 EXPLORATEUR DE VOCABULAIRE")
    print("=" * 40)
    
    # Initialiser le MixPlayer
    mix_player = MixPlayer()
    
    print("🎵 Chargement des transcriptions...")
    mix_player.load_transcriptions()
    
    # Statistiques générales
    total_words = sum(len(matches) for matches in mix_player.word_index.values())
    unique_words = len(mix_player.word_index)
    
    print(f"📚 {total_words} mots indexés ({unique_words} mots uniques)")
    print()
    
    # Afficher quelques mots par catégorie
    print("🎯 ÉCHANTILLON DU VOCABULAIRE:")
    print("-" * 30)
    
    # Trier les mots par ordre alphabétique
    sorted_words = sorted(mix_player.word_index.keys())
    
    # Afficher les premiers mots
    print("📝 Premiers mots (A-C):")
    for word in sorted_words[:20]:
        example_match = mix_player.word_index[word][0]
        count = len(mix_player.word_index[word])
        print(f"  • {example_match.word} ({word}) - {count} occurrences")
    
    print("\n🔤 Mots courts (1-3 lettres):")
    short_words = [w for w in sorted_words if len(w) <= 3][:15]
    for word in short_words:
        example_match = mix_player.word_index[word][0]
        count = len(mix_player.word_index[word])
        print(f"  • {example_match.word} ({word}) - {count} occurrences")
    
    print("\n💝 Mots d'amour/émotion:")
    love_words = []
    emotion_keywords = ['amour', 'coeur', 'aime', 'love', 'emotion', 'sentiment', 'passion', 'tendresse', 'affection']
    
    for word in sorted_words:
        for keyword in emotion_keywords:
            if keyword in word.lower():
                love_words.append(word)
                break
    
    for word in love_words[:10]:
        example_match = mix_player.word_index[word][0]
        count = len(mix_player.word_index[word])
        print(f"  • {example_match.word} ({word}) - {count} occurrences")
    
    print("\n🎼 Mots musicaux/artistiques:")
    music_words = []
    music_keywords = ['music', 'son', 'melodie', 'chant', 'rythme', 'note', 'voix', 'art', 'belle', 'beaute']
    
    for word in sorted_words:
        for keyword in music_keywords:
            if keyword in word.lower():
                music_words.append(word)
                break
    
    for word in music_words[:10]:
        example_match = mix_player.word_index[word][0]
        count = len(mix_player.word_index[word])
        print(f"  • {example_match.word} ({word}) - {count} occurrences")
    
    # Recherche interactive
    print("\n" + "=" * 40)
    print("🔍 RECHERCHE INTERACTIVE")
    print("Tapez un mot pour voir s'il existe, ou 'quit' pour quitter")
    
    while True:
        search_term = input("\n🔎 Rechercher: ").strip()
        
        if search_term.lower() in ['quit', 'exit', 'q']:
            break
        
        if not search_term:
            continue
        
        # Recherche exacte
        cleaned_search = mix_player.clean_word(search_term)
        exact_matches = mix_player.word_index.get(cleaned_search, [])
        
        if exact_matches:
            print(f"✅ Trouvé '{search_term}' - {len(exact_matches)} occurrences:")
            for match in exact_matches[:5]:
                print(f"  📁 {Path(match.file_name).stem} - {match.speaker} - {match.start:.1f}s")
        else:
            print(f"❌ '{search_term}' non trouvé")
            
            # Suggestions similaires
            similar = difflib.get_close_matches(
                cleaned_search, 
                mix_player.word_index.keys(), 
                n=5, 
                cutoff=0.6
            )
            
            if similar:
                print("💡 Mots similaires disponibles:")
                for sim_word in similar:
                    example = mix_player.word_index[sim_word][0]
                    print(f"  • {example.word} ({sim_word})")

def search_vocabulary_pattern(pattern: str):
    """Recherche des mots correspondant à un motif"""
    
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    print(f"🔍 Recherche de mots contenant '{pattern}':")
    print("-" * 40)
    
    matching_words = []
    for word_key in mix_player.word_index.keys():
        if pattern.lower() in word_key.lower():
            matching_words.append(word_key)
    
    if matching_words:
        matching_words.sort()
        print(f"✅ {len(matching_words)} mots trouvés:")
        
        for word in matching_words[:20]:  # Limite à 20 résultats
            example_match = mix_player.word_index[word][0]
            count = len(mix_player.word_index[word])
            print(f"  • {example_match.word} ({word}) - {count} occurrences")
        
        if len(matching_words) > 20:
            print(f"  ... et {len(matching_words) - 20} autres")
    else:
        print(f"❌ Aucun mot contenant '{pattern}' trouvé")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Mode recherche de motif
        pattern = sys.argv[1]
        search_vocabulary_pattern(pattern)
    else:
        # Mode exploration interactive
        explore_vocabulary()