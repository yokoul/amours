#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la diversification des sources dans le Mix-Play
Valide que les mots répétés proviennent de sources différentes
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mix_player import MixPlayer

def test_source_diversity():
    """Test la diversité des sources avec des mots répétés"""
    
    print("🔄 TEST DE DIVERSIFICATION DES SOURCES")
    print("=" * 40)
    
    # Initialiser le MixPlayer
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrase avec des mots répétés pour tester la diversification
    test_phrases = [
        # Phrase avec beaucoup de répétitions
        "avec avec avec avec tout tout tout amour amour amour je je je",
        
        # Phrase avec mots courants répétés
        "la la la le le le de de de et et et",
        
        # Phrase plus naturelle avec quelques répétitions
        "avec tout mon amour je vois la vie avec tout mon amour",
        
        # Test phrase originale pour comparaison
        "avec tout cet amour je vois le bonheur comme une mélodie"
    ]
    
    for i, test_phrase in enumerate(test_phrases, 1):
        print(f"\n🧪 TEST {i}: {test_phrase}")
        print("-" * 50)
        
        words = test_phrase.split()
        
        # Test avec diversification activée
        print("🎯 AVEC DIVERSIFICATION DES SOURCES:")
        composed_diverse = mix_player.compose_sentence(
            words,
            min_confidence=0.5,
            prioritize_diversity=True
        )
        
        print("🎯 SANS DIVERSIFICATION DES SOURCES:")
        composed_standard = mix_player.compose_sentence(
            words,
            min_confidence=0.5,
            prioritize_diversity=False
        )
        
        # Analyser la diversité
        analyze_diversity(composed_diverse, "Avec diversification")
        analyze_diversity(composed_standard, "Sans diversification")
        
        print("=" * 50)

def analyze_diversity(composed, mode_name):
    """Analyse la diversité des sources dans une composition"""
    
    print(f"\n📊 ANALYSE - {mode_name}:")
    print("-" * 30)
    
    if not composed.words:
        print("❌ Aucun mot trouvé")
        return
    
    # Compter les sources utilisées
    source_usage = {}
    word_details = {}
    
    for i, word_match in enumerate(composed.words):
        source_key = f"{Path(word_match.file_name).stem}_{word_match.speaker}"
        word = word_match.word.strip()
        
        # Compter l'usage des sources
        source_usage[source_key] = source_usage.get(source_key, 0) + 1
        
        # Enregistrer les détails pour chaque mot
        if word not in word_details:
            word_details[word] = []
        
        word_details[word].append({
            'source': source_key,
            'position': i + 1,
            'confidence': word_match.confidence,
            'time': word_match.start
        })
    
    # Afficher les statistiques générales
    total_sources_available = len(source_usage)
    max_usage = max(source_usage.values()) if source_usage else 0
    overused_sources = sum(1 for count in source_usage.values() if count > 1)
    
    print(f"🎯 Sources différentes utilisées: {total_sources_available}")
    print(f"🔄 Sources réutilisées: {overused_sources}")
    print(f"📈 Usage maximum d'une source: {max_usage} fois")
    
    # Détailler les mots répétés
    repeated_words = {word: details for word, details in word_details.items() 
                     if len(details) > 1}
    
    if repeated_words:
        print(f"\n🔍 MOTS RÉPÉTÉS ({len(repeated_words)}):")
        
        for word, details in repeated_words.items():
            print(f"  📝 '{word}' ({len(details)} occurrences):")
            
            sources_used = set()
            for detail in details:
                source_indicator = "🆕" if detail['source'] not in sources_used else "🔄"
                sources_used.add(detail['source'])
                
                print(f"     {source_indicator} Pos.{detail['position']} - {detail['source']} "
                      f"(conf: {detail['confidence']:.1f}%)")
            
            # Calculer le taux de diversification pour ce mot
            diversity_rate = len(sources_used) / len(details) * 100
            diversity_emoji = "🌟" if diversity_rate >= 75 else "⚠️" if diversity_rate >= 50 else "❌"
            print(f"     {diversity_emoji} Diversité: {diversity_rate:.0f}% "
                  f"({len(sources_used)}/{len(details)} sources différentes)")
    else:
        print("✨ Aucun mot répété - pas de test de diversification nécessaire")
    
    # Score global de diversification
    if source_usage:
        total_words = sum(source_usage.values())
        ideal_distribution = total_words / len(source_usage)
        
        # Calculer l'écart-type pour mesurer la distribution
        variance = sum((count - ideal_distribution) ** 2 for count in source_usage.values()) / len(source_usage)
        std_dev = variance ** 0.5
        
        # Score de diversification (0-100, 100 = parfaitement distribué)
        max_possible_std = (total_words - 1) / 2  # Pire cas théorique
        diversity_score = max(0, (1 - std_dev / max_possible_std) * 100) if max_possible_std > 0 else 100
        
        score_emoji = "🌟" if diversity_score >= 80 else "👍" if diversity_score >= 60 else "⚠️"
        print(f"{score_emoji} Score de diversification: {diversity_score:.1f}%")

def compare_algorithms():
    """Compare les deux approches côte à côte"""
    
    print("\n⚖️ COMPARAISON DIRECTE DES ALGORITHMES")
    print("=" * 45)
    
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrase avec répétitions pour test optimal
    test_phrase = "avec tout mon amour avec tout mon amour je vois la vie"
    words = test_phrase.split()
    
    print(f"🎯 Phrase de test: {test_phrase}")
    print(f"🔢 Mots répétés: {len(words) - len(set(words))} répétitions")
    print()
    
    # Version avec diversification
    print("🌟 ALGORITHME AVEC DIVERSIFICATION:")
    composed_diverse = mix_player.compose_sentence(
        words, 
        prioritize_diversity=True,
        min_confidence=0.4
    )
    
    print("🔄 ALGORITHME STANDARD (sans diversification):")
    composed_standard = mix_player.compose_sentence(
        words,
        prioritize_diversity=False, 
        min_confidence=0.4
    )
    
    # Comparaison finale
    print("🏆 VERDICT:")
    if composed_diverse.words and composed_standard.words:
        diverse_sources = len(set(f"{Path(w.file_name).stem}_{w.speaker}" for w in composed_diverse.words))
        standard_sources = len(set(f"{Path(w.file_name).stem}_{w.speaker}" for w in composed_standard.words))
        
        print(f"   Diversifié: {diverse_sources} sources différentes")
        print(f"   Standard: {standard_sources} sources différentes")
        
        if diverse_sources > standard_sources:
            print("   ✅ La diversification améliore la variété des sources!")
        elif diverse_sources == standard_sources:
            print("   ⚖️ Même niveau de diversité dans les deux cas")
        else:
            print("   ⚠️ L'algorithme standard était déjà assez diversifié")

if __name__ == "__main__":
    test_source_diversity()
    compare_algorithms()