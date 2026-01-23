"""
Diagnostic de la recherche de mots - Vérification des timecodes et correspondances.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def diagnose_word_search():
    """Diagnostic détaillé de la recherche de mots."""
    
    print("🔍 DIAGNOSTIC DE LA RECHERCHE DE MOTS")
    print("=" * 45)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # La phrase problématique
    test_phrase = "avec tout cet amour, je vois le bonheur comme une mélodie"
    words = test_phrase.replace(',', '').split()  # Supprimer la ponctuation
    
    print(f"🎯 Phrase originale: {test_phrase}")
    print(f"🔤 Mots recherchés: {words}")
    print()
    
    # Analyser chaque mot individuellement
    print("📊 ANALYSE DÉTAILLÉE PAR MOT:")
    print("-" * 35)
    
    for i, word in enumerate(words, 1):
        print(f"\n{i}. Recherche de '{word}':")
        
        # Recherche avec plus de détails
        matches = mix_player.search_word(word, max_results=5)
        
        if matches:
            print(f"   ✅ {len(matches)} correspondances trouvées:")
            for j, match in enumerate(matches, 1):
                print(f"      {j}. '{match.word}' (nettoyé: '{match.cleaned_word}')")
                print(f"         📁 {Path(match.file_name).stem}")
                print(f"         🎭 {match.speaker}")
                print(f"         ⏱️  {match.start:.2f}s - {match.end:.2f}s")
                print(f"         🎯 Confiance: {match.confidence:.1%}")
                
                # Vérifier si c'est une vraie correspondance
                word_clean = mix_player.clean_word(word)
                if word_clean != match.cleaned_word:
                    print(f"         ⚠️  ATTENTION: '{word_clean}' != '{match.cleaned_word}'")
                print()
        else:
            print(f"   ❌ Aucune correspondance trouvée")
            
            # Chercher des mots similaires
            import difflib
            all_words = list(mix_player.word_index.keys())
            word_clean = mix_player.clean_word(word)
            similar = difflib.get_close_matches(word_clean, all_words, n=3, cutoff=0.6)
            
            if similar:
                print(f"   🔍 Mots similaires disponibles:")
                for sim in similar:
                    example_match = mix_player.word_index[sim][0]
                    print(f"      - '{example_match.word}' (similaire à '{word}')")
    
    print(f"\n" + "="*50)
    
    # Maintenant testons la composition complète
    print(f"\n🎭 COMPOSITION AUTOMATIQUE:")
    print("-" * 25)
    
    composed = mix_player.compose_sentence(words, min_confidence=0.5)
    
    print(f"📝 Résultat brut: {composed.text}")
    print(f"🔤 Mots trouvés: {len(composed.words)}/{len(words)}")
    print()
    
    if composed.words:
        print("📋 DÉTAIL DES MOTS SÉLECTIONNÉS:")
        for i, word_match in enumerate(composed.words, 1):
            original_word = words[i-1] if i <= len(words) else "???"
            print(f"{i}. Cherché: '{original_word}' → Trouvé: '{word_match.word.strip()}'")
            print(f"   📁 {Path(word_match.file_name).stem}")
            print(f"   🎭 {word_match.speaker}")
            print(f"   ⏱️  {word_match.start:.2f}s - {word_match.end:.2f}s")
            print(f"   🎯 {word_match.confidence:.1%}")
            
            # Vérifier la correspondance
            searched_clean = mix_player.clean_word(original_word)
            found_clean = word_match.cleaned_word
            
            if searched_clean != found_clean:
                print(f"   ⚠️  PROBLÈME: '{searched_clean}' != '{found_clean}'")
            else:
                print(f"   ✅ Correspondance correcte")
            print()
    
    print(f"\n💡 SUGGESTIONS POUR AMÉLIORER:")
    print("• Utilisez des mots plus courants du vocabulaire disponible")
    print("• Vérifiez les mots disponibles avec vocabulary_explorer.py")
    print("• Réduisez le seuil de confiance si nécessaire")
    
    return composed


def test_specific_words():
    """Test avec des mots spécifiques connus."""
    print(f"\n🧪 TEST AVEC MOTS CONNUS:")
    print("-" * 30)
    
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Mots qu'on sait être présents (vus dans les tests précédents)
    known_words = ["avec", "tout", "mon", "amour", "bonjour", "la", "vie"]
    
    for word in known_words:
        matches = mix_player.search_word(word, max_results=1)
        if matches:
            match = matches[0]
            print(f"✅ '{word}' → '{match.word}' ({match.confidence:.1%}) à {match.start:.1f}s")
        else:
            print(f"❌ '{word}' non trouvé")
    
    # Test de composition avec ces mots connus
    test_composed = mix_player.compose_sentence(known_words[:4], min_confidence=0.6)
    print(f"\n🎵 Test composition: {test_composed.text}")


if __name__ == "__main__":
    composed = diagnose_word_search()
    test_specific_words()
    
    if composed.words:
        print(f"\n🎧 Voulez-vous écouter le résultat pour vérifier ?")
        listen = input("Générer et écouter l'audio ? (O/n): ").strip().lower()
        
        if listen not in ['n', 'non', 'no']:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H%M%S")
            output_file = f"output_mix_play/diagnostic_{timestamp}.mp3"
            
            try:
                audio_file = mix_player.generate_mixed_audio(
                    composed, output_file,
                    word_padding=0.15, fade_mode="standard"
                )
                
                print(f"🎵 Généré: {Path(audio_file).name}")
                
                import subprocess
                import platform
                if platform.system() == "Darwin":
                    subprocess.run(["afplay", audio_file])
                    print("✅ Écoute terminée")
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")