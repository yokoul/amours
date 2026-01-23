#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur en batch pour tests massifs du système Mix-Play
"""

import sys
from pathlib import Path
from datetime import datetime
import re
import json

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mix_player import MixPlayer

def batch_generation():
    """Génération en batch de multiples variantes"""
    
    print("🔄 GÉNÉRATEUR BATCH MIX-PLAY")
    print("=" * 30)
    
    # Initialisation
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    output_dir = Path("output_mix_play/batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collection de phrases de test
    test_phrases = [
        # Phrases d'amour
        "avec tout mon amour je te dis bonjour",
        "je t aime de tout mon coeur",
        "tu es la lumière de ma vie",
        
        # Phrases de salutation
        "bonjour comment allez vous aujourd hui",
        "bonne journée à vous tous",
        "je vous souhaite le meilleur",
        
        # Phrases poétiques
        "la vie est belle comme une chanson",
        "je vois la lumière dans tes yeux",
        "le bonheur nous accompagne chaque jour",
        
        # Test répétitions (diversification)
        "avec avec avec tout tout tout amour amour amour",
        "la la la vie vie vie est est est belle belle belle",
        "je je je te te te dis dis dis bonjour bonjour bonjour",
        
        # Phrases longues
        "aujourd hui est un jour magnifique pour dire je t aime",
        "avec tout cet amour dans mon coeur je te souhaite le bonheur",
        
        # Phrases courtes
        "bonjour",
        "je t aime",
        "bonne journée",
        "merci beaucoup"
    ]
    
    # Configuration des tests
    test_configs = [
        {
            "name": "standard",
            "params": {
                "prioritize_diversity": False,
                "min_confidence": 0.4,
                "fade_mode": "standard",
                "tempo_factor": 1.0
            }
        },
        {
            "name": "diversified",
            "params": {
                "prioritize_diversity": True,
                "min_confidence": 0.4,
                "fade_mode": "standard", 
                "tempo_factor": 1.0
            }
        },
        {
            "name": "artistic_slow",
            "params": {
                "prioritize_diversity": True,
                "min_confidence": 0.3,
                "fade_mode": "artistic",
                "tempo_factor": 0.8
            }
        },
        {
            "name": "seamless_fast",
            "params": {
                "prioritize_diversity": True,
                "min_confidence": 0.5,
                "fade_mode": "seamless",
                "tempo_factor": 1.2
            }
        }
    ]
    
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"🎯 {len(test_phrases)} phrases × {len(test_configs)} configs = {len(test_phrases) * len(test_configs)} générations")
    print()
    
    total_generated = 0
    total_errors = 0
    
    for phrase_idx, phrase in enumerate(test_phrases, 1):
        print(f"\n📝 [{phrase_idx:2d}/{len(test_phrases)}] {phrase}")
        print("-" * 50)
        
        # Nettoyer la phrase
        words = re.findall(r'\b\w+\b', phrase.lower())
        
        for config in test_configs:
            config_name = config["name"]
            
            try:
                # Composer la phrase
                composed = mix_player.compose_sentence(
                    words,
                    prioritize_diversity=config["params"]["prioritize_diversity"],
                    min_confidence=config["params"]["min_confidence"]
                )
                
                if not composed.words:
                    print(f"  ❌ {config_name}: Aucun mot trouvé")
                    results.append({
                        "phrase": phrase,
                        "config": config_name,
                        "status": "no_words",
                        "words_found": 0,
                        "words_total": len(words)
                    })
                    continue
                
                # Générer l'audio
                safe_phrase = re.sub(r'[^\w\s]', '', phrase)[:30].replace(' ', '_')
                filename = f"{phrase_idx:02d}_{safe_phrase}_{config_name}_{timestamp}.mp3"
                
                audio_file = mix_player.generate_mixed_audio(
                    composed,
                    str(output_dir / filename),
                    fade_mode=config["params"]["fade_mode"],
                    tempo_factor=config["params"]["tempo_factor"],
                    word_padding=0.1
                )
                
                total_generated += 1
                
                # Statistiques
                sources_used = len(set(f"{Path(w.file_name).stem}_{w.speaker}" for w in composed.words))
                
                print(f"  ✅ {config_name}: {len(composed.words)}/{len(words)} mots, {sources_used} sources")
                
                results.append({
                    "phrase": phrase,
                    "config": config_name, 
                    "status": "success",
                    "words_found": len(composed.words),
                    "words_total": len(words),
                    "sources_used": sources_used,
                    "filename": filename,
                    "text_generated": composed.text,
                    "duration": composed.total_duration
                })
                
            except Exception as e:
                total_errors += 1
                print(f"  ❌ {config_name}: Erreur - {e}")
                results.append({
                    "phrase": phrase,
                    "config": config_name,
                    "status": "error",
                    "error": str(e)
                })
    
    # Sauvegarder les résultats
    report_file = output_dir / f"batch_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 RÉSUMÉ DE LA GÉNÉRATION BATCH")
    print("=" * 35)
    print(f"✅ Fichiers générés: {total_generated}")
    print(f"❌ Erreurs: {total_errors}")
    print(f"📂 Dossier: {output_dir}")
    print(f"📋 Rapport: {report_file.name}")
    
    # Statistiques par configuration
    print(f"\n📈 STATISTIQUES PAR CONFIGURATION:")
    for config in test_configs:
        config_results = [r for r in results if r["config"] == config["name"]]
        successes = [r for r in config_results if r["status"] == "success"]
        
        if successes:
            avg_words = sum(r["words_found"] for r in successes) / len(successes)
            avg_sources = sum(r["sources_used"] for r in successes) / len(successes)
            
            print(f"  {config['name']:15} : {len(successes):2d} succès, "
                  f"{avg_words:.1f} mots moy., {avg_sources:.1f} sources moy.")
    
    # Top phrases qui fonctionnent le mieux
    print(f"\n🏆 TOP PHRASES PAR RÉUSSITE:")
    phrase_stats = {}
    for phrase in test_phrases:
        phrase_results = [r for r in results if r["phrase"] == phrase and r["status"] == "success"]
        if phrase_results:
            phrase_stats[phrase] = len(phrase_results)
    
    top_phrases = sorted(phrase_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for phrase, count in top_phrases:
        print(f"  {count}/4 : {phrase}")

def quick_batch():
    """Version rapide avec quelques phrases seulement"""
    
    print("⚡ BATCH RAPIDE")
    print("-" * 15)
    
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    output_dir = Path("output_mix_play/quick")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    quick_phrases = [
        "bonjour comment allez vous",
        "je vous souhaite une belle journée", 
        "avec tout mon amour"
    ]
    
    for i, phrase in enumerate(quick_phrases, 1):
        print(f"\n{i}. {phrase}")
        words = re.findall(r'\b\w+\b', phrase.lower())
        
        # Test diversifié seulement
        composed = mix_player.compose_sentence(
            words, 
            prioritize_diversity=True,
            min_confidence=0.3
        )
        
        if composed.words:
            filename = f"quick_{i:02d}_{datetime.now().strftime('%H%M%S')}.mp3"
            audio_file = mix_player.generate_mixed_audio(
                composed,
                str(output_dir / filename),
                fade_mode="artistic",
                word_padding=0.1
            )
            print(f"   ✅ {filename}")
        else:
            print("   ❌ Aucun mot trouvé")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_batch()
    else:
        batch_generation()