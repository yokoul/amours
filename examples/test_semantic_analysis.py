#!/usr/bin/env python3
"""
Test de l'analyse d'amour avec sentence-transformers.
"""

import sys
import os
from pathlib import Path

# Ajouter src au PATH
current_dir = Path(__file__).parent.parent  # Remonter au répertoire racine
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from love_analyzer import LoveTypeAnalyzer


def test_semantic_analysis():
    """Test l'analyse sémantique avec des exemples."""
    print("🧪 Test de l'analyse sémantique avec sentence-transformers")
    print("=" * 70)
    
    # Tenter d'installer sentence-transformers si nécessaire
    try:
        import sentence_transformers
        print("✅ sentence-transformers disponible")
    except ImportError:
        print("⚠️  sentence-transformers non installé. Installation en cours...")
        os.system("pip install sentence-transformers")
        try:
            import sentence_transformers
            print("✅ sentence-transformers installé avec succès")
        except ImportError:
            print("❌ Impossible d'installer sentence-transformers")
            return
    
    # Initialiser l'analyseur avec sémantique activée
    print("\n🤖 Initialisation de l'analyseur avec analyse sémantique...")
    analyzer = LoveTypeAnalyzer(min_score_threshold=0.05, use_semantic_analysis=True)
    
    # Phrases de test pour différents types d'amour
    test_phrases = [
        # Romantique
        ("Tu es l'amour de ma vie, mon âme sœur, je t'aime passionnément", "romantique"),
        ("Je rêve de toi chaque nuit, tu es si belle et romantique", "romantique"),
        
        # Familial
        ("J'aime mes parents et mes enfants de tout mon cœur", "familial"),
        ("L'amour familial est ce qu'il y a de plus important", "familial"),
        
        # Amical
        ("J'adore mes amis, on s'amuse bien ensemble", "amical"),
        ("L'amitié c'est sacré, mes copains sont géniaux", "amical"),
        
        # Érotique
        ("Je te désire ardemment, ton corps me fait chavirer", "erotique"),
        ("Cette attraction physique est intense et sensuelle", "erotique"),
        
        # Compassionnel
        ("J'ai pitié de lui, je veux l'aider et le sauver", "compassionnel"),
        ("Mon cœur saigne pour tous ceux qui souffrent", "compassionnel"),
        
        # Narcissique
        ("Je m'aime tel que je suis, je suis parfait et unique", "narcissique"),
        ("Elle m'appartient, elle est à moi et je la possède", "narcissique"),
        
        # Platonique
        ("Je l'admire de loin, c'est un amour pur et spirituel", "platonique"),
        ("Cette personne m'inspire, c'est un amour idéalisé", "platonique"),
        
        # Neutre (pour contrôle)
        ("Il fait beau aujourd'hui, je vais aller faire des courses", "neutre"),
        ("La réunion de demain est reportée à jeudi prochain", "neutre")
    ]
    
    print(f"\n📊 RÉSULTATS DES TESTS ({len(test_phrases)} phrases)")
    print("=" * 70)
    
    correct_predictions = 0
    total_tests = len(test_phrases)
    
    for i, (phrase, expected_type) in enumerate(test_phrases, 1):
        print(f"\n{i}. Phrase: \"{phrase}\"")
        print(f"   Type attendu: {expected_type}")
        
        # Analyser
        scores = analyzer.analyze_segment(phrase)
        
        # Trouver le type dominant
        if max(scores.values()) > analyzer.min_score_threshold:
            dominant_type = max(scores, key=scores.get)
            confidence = scores[dominant_type]
        else:
            dominant_type = "neutre"
            confidence = 0.0
        
        print(f"   Type détecté: {dominant_type} (confiance: {confidence:.3f})")
        
        # Afficher les top 3 des scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"   Top 3 scores: {', '.join([f'{t}:{s:.3f}' for t, s in sorted_scores])}")
        
        # Vérifier la prédiction
        is_correct = (expected_type == "neutre" and confidence <= analyzer.min_score_threshold) or \
                    (expected_type != "neutre" and dominant_type == expected_type)
        
        if is_correct:
            correct_predictions += 1
            print("   ✅ CORRECT")
        else:
            print("   ❌ INCORRECT")
    
    # Statistiques finales
    accuracy = (correct_predictions / total_tests) * 100
    print(f"\n📈 STATISTIQUES FINALES")
    print("=" * 70)
    print(f"Prédictions correctes: {correct_predictions}/{total_tests}")
    print(f"Précision: {accuracy:.1f}%")
    
    if accuracy >= 70:
        print("🎉 Excellente performance !")
    elif accuracy >= 50:
        print("✅ Performance acceptable")
    else:
        print("⚠️  Performance à améliorer")
    
    # Test sur données réelles si disponibles
    print(f"\n🎯 Test sur données réelles")
    print("-" * 40)
    test_with_real_data(analyzer)


def test_with_real_data(analyzer):
    """Test sur des données de transcription réelles."""
    import json
    
    # Chercher des fichiers JSON existants
    output_dirs = [
        Path("output"),
        Path("output_v1"), 
        Path("output_v2")
    ]
    
    json_files = []
    for output_dir in output_dirs:
        if output_dir.exists():
            json_files.extend(output_dir.glob("*_complete.json"))
    
    if not json_files:
        print("❌ Aucun fichier de transcription trouvé")
        return
    
    # Prendre le premier fichier
    test_file = json_files[0]
    print(f"📁 Analyse du fichier: {test_file.name}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data['transcription']['segments'][:10]  # Analyser seulement 10 segments
        
        total_love_detected = 0
        for i, segment in enumerate(segments, 1):
            text = segment['text']
            scores = analyzer.analyze_segment(text)
            
            max_score = max(scores.values())
            if max_score > analyzer.min_score_threshold:
                dominant_type = max(scores, key=scores.get)
                total_love_detected += 1
                
                print(f"{i}. \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
                print(f"   → {dominant_type}: {max_score:.3f}")
                print()
        
        detection_rate = (total_love_detected / len(segments)) * 100
        print(f"📊 Résumé: {total_love_detected}/{len(segments)} segments avec amour détecté ({detection_rate:.1f}%)")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")


if __name__ == "__main__":
    test_semantic_analysis()