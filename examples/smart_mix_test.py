"""
Générateur de phrases intelligentes avec optimisation contextuelle.

Ce module améliore la sélection des mots en privilégiant la cohérence contextuelle.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer, WordMatch, ComposedSentence


class SmartMixPlayer(MixPlayer):
    """Version améliorée du MixPlayer avec sélection contextuelle intelligente."""
    
    def find_contextual_sequence(self, words: List[str], 
                               min_confidence: float = 0.7,
                               max_time_gap: float = 10.0,
                               same_speaker_bonus: float = 0.1) -> ComposedSentence:
        """
        Trouve la meilleure séquence de mots en privilégiant le contexte.
        
        Args:
            words: Liste des mots à rechercher
            min_confidence: Confiance minimum
            max_time_gap: Écart maximum entre deux mots consécutifs (secondes)
            same_speaker_bonus: Bonus de score pour le même locuteur
        """
        if not words:
            return ComposedSentence("", [], 0.0, [], [])
        
        # Obtenir toutes les correspondances possibles pour chaque mot
        all_matches = {}
        for word in words:
            matches = self.search_word(word, max_results=20)
            matches = [m for m in matches if m.confidence >= min_confidence]
            all_matches[word] = matches
        
        # Vérifier qu'on a au moins une correspondance pour chaque mot
        missing_words = [w for w in words if not all_matches.get(w)]
        if missing_words:
            print(f"⚠️ Mots manquants avec confiance {min_confidence}: {missing_words}")
        
        # Si on n'a pas tous les mots, utiliser la méthode classique
        if missing_words:
            return self.compose_sentence(words, min_confidence=min_confidence * 0.8)
        
        print(f"🧠 Recherche de séquence contextuelle pour {len(words)} mots...")
        
        # Algorithme de sélection contextuelle
        best_sequence = self._find_best_contextual_sequence(
            words, all_matches, max_time_gap, same_speaker_bonus
        )
        
        if not best_sequence:
            print("⚠️ Aucune séquence contextuelle trouvée, utilisation de la méthode classique")
            return self.compose_sentence(words, min_confidence=min_confidence)
        
        # Calculer les statistiques
        total_duration = sum(w.duration for w in best_sequence) + 0.3 * (len(best_sequence) - 1)
        speakers_used = list(set(w.speaker for w in best_sequence))
        files_used = list(set(w.file_name for w in best_sequence))
        composed_text = " ".join(w.word.strip() for w in best_sequence)
        
        return ComposedSentence(
            text=composed_text,
            words=best_sequence,
            total_duration=total_duration,
            speakers_used=speakers_used,
            files_used=files_used
        )
    
    def _find_best_contextual_sequence(self, words: List[str], 
                                     all_matches: Dict[str, List[WordMatch]],
                                     max_time_gap: float,
                                     same_speaker_bonus: float) -> List[WordMatch]:
        """Trouve la meilleure séquence contextuelle par programmation dynamique."""
        
        n = len(words)
        if n == 0:
            return []
        
        # Cas simple : un seul mot
        if n == 1:
            matches = all_matches[words[0]]
            return [max(matches, key=lambda x: x.confidence)] if matches else []
        
        # Pour des séquences courtes, on teste toutes les combinaisons
        if n <= 4:
            return self._brute_force_best_sequence(words, all_matches, max_time_gap, same_speaker_bonus)
        
        # Pour des séquences plus longues, approche gloutonne
        return self._greedy_contextual_sequence(words, all_matches, max_time_gap, same_speaker_bonus)
    
    def _brute_force_best_sequence(self, words: List[str], 
                                 all_matches: Dict[str, List[WordMatch]],
                                 max_time_gap: float,
                                 same_speaker_bonus: float) -> List[WordMatch]:
        """Test toutes les combinaisons possibles pour trouver la meilleure séquence."""
        
        import itertools
        
        # Générer toutes les combinaisons possibles
        combinations = list(itertools.product(*[all_matches[word][:10] for word in words]))
        
        best_sequence = None
        best_score = -1
        
        for combination in combinations:
            score = self._score_sequence(combination, max_time_gap, same_speaker_bonus)
            if score > best_score:
                best_score = score
                best_sequence = combination
        
        return list(best_sequence) if best_sequence else []
    
    def _greedy_contextual_sequence(self, words: List[str], 
                                  all_matches: Dict[str, List[WordMatch]],
                                  max_time_gap: float,
                                  same_speaker_bonus: float) -> List[WordMatch]:
        """Approche gloutonne pour les longues séquences."""
        
        sequence = []
        
        # Commencer par le mot avec le plus de correspondances de haute qualité
        first_word = max(words, key=lambda w: len([m for m in all_matches[w] if m.confidence > 0.8]))
        first_matches = all_matches[first_word]
        current_match = max(first_matches, key=lambda x: x.confidence)
        sequence.append(current_match)
        
        # Sélectionner les mots restants
        remaining_words = [w for w in words if w != first_word]
        
        while remaining_words:
            best_next_word = None
            best_next_match = None
            best_score = -1
            
            for word in remaining_words:
                for match in all_matches[word][:5]:  # Top 5 matches seulement
                    test_sequence = sequence + [match]
                    score = self._score_sequence(test_sequence, max_time_gap, same_speaker_bonus)
                    
                    if score > best_score:
                        best_score = score
                        best_next_word = word
                        best_next_match = match
            
            if best_next_match:
                sequence.append(best_next_match)
                remaining_words.remove(best_next_word)
            else:
                # Si aucune correspondance acceptable, prendre la meilleure disponible
                word = remaining_words[0]
                sequence.append(max(all_matches[word], key=lambda x: x.confidence))
                remaining_words.remove(word)
        
        return sequence
    
    def _score_sequence(self, sequence: List[WordMatch], 
                       max_time_gap: float, 
                       same_speaker_bonus: float) -> float:
        """Calcule le score d'une séquence de mots."""
        
        if not sequence:
            return 0
        
        # Score de base : moyenne des confidences
        base_score = sum(match.confidence for match in sequence) / len(sequence)
        
        # Bonus pour la cohérence du locuteur
        speakers = [match.speaker for match in sequence]
        unique_speakers = set(speakers)
        
        if len(unique_speakers) == 1:
            base_score += same_speaker_bonus * 2  # Même locuteur partout
        elif len(unique_speakers) == 2:
            base_score += same_speaker_bonus      # Seulement 2 locuteurs
        
        # Pénalité pour les écarts temporels trop importants
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_word = sequence[i + 1]
            
            # Si même fichier, vérifier l'écart temporel
            if current.file_name == next_word.file_name:
                time_gap = abs(next_word.start - current.end)
                if time_gap > max_time_gap:
                    penalty = min(0.2, time_gap / max_time_gap * 0.1)
                    base_score -= penalty
                else:
                    # Bonus pour la proximité temporelle
                    proximity_bonus = max(0, (max_time_gap - time_gap) / max_time_gap * 0.05)
                    base_score += proximity_bonus
        
        # Bonus pour la variété des fichiers sources (mais pas trop)
        unique_files = set(match.file_name for match in sequence)
        if len(unique_files) == 2:
            base_score += 0.02  # Léger bonus pour 2 sources
        elif len(unique_files) > 3:
            base_score -= 0.05  # Pénalité pour trop de sources
        
        return base_score


def test_smart_mix():
    """Test du générateur intelligent."""
    
    print("🧠 Test du Mix-Play Intelligent")
    print("=" * 35)
    
    smart_player = SmartMixPlayer()
    smart_player.load_transcriptions()
    
    test_phrases = [
        "bonjour mon amour",
        "la vie est belle",
        "avec tout mon coeur",
        "dans le monde entier"
    ]
    
    for phrase in test_phrases:
        print(f"\n🎯 Test: {phrase}")
        print("-" * (len(phrase) + 10))
        
        # Méthode classique
        classic = smart_player.compose_sentence(phrase.split(), min_confidence=0.6)
        print(f"📝 Classique: {classic.text}")
        print(f"   🎭 {len(classic.speakers_used)} locuteurs, {len(classic.files_used)} fichiers")
        
        # Méthode intelligente
        smart = smart_player.find_contextual_sequence(phrase.split(), min_confidence=0.6)
        print(f"🧠 Intelligent: {smart.text}")
        print(f"   🎭 {len(smart.speakers_used)} locuteurs, {len(smart.files_used)} fichiers")
        
        # Générer les deux versions audio
        if classic.words and smart.words:
            timestamp = datetime.now().strftime("%H%M%S")
            
            classic_file = f"output_mix_play/classic_{phrase.replace(' ', '_')}_{timestamp}.mp3"
            smart_file = f"output_mix_play/smart_{phrase.replace(' ', '_')}_{timestamp}.mp3"
            
            try:
                smart_player.generate_mixed_audio(classic, classic_file, word_padding=0.2)
                smart_player.generate_mixed_audio(smart, smart_file, word_padding=0.2)
                print(f"   🎵 Audio généré: classic vs smart")
            except Exception as e:
                print(f"   ❌ Erreur audio: {e}")


if __name__ == "__main__":
    test_smart_mix()