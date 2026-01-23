"""
Module de reconstruction des phrases complètes à partir des segments Whisper.
Regroupe les segments pour former des phrases syntaxiquement cohérentes.
"""

import re
from typing import List, Dict, Any
from collections import defaultdict


class SentenceReconstructor:
    """Reconstruit des phrases complètes à partir de segments fragmentés."""
    
    def __init__(self):
        """Initialise le reconstructeur."""
        # Marqueurs de fin de phrase
        self.sentence_endings = {'.', '!', '?', '...', '…'}
        
        # Marqueurs de continuation (ne pas couper après)
        self.continuation_patterns = [
            r'\b(M|Mme|Dr|Prof|St|Ste)\.',  # Abréviations
            r'\b\w\.',  # Initiales
            r'\d+\.',   # Numéros
            r'etc\.',   # etc.
            r'c\'est-à-dire',
            r'c-à-d',
        ]
        
        # Mots qui indiquent une continuation
        self.continuation_words = {
            'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'puis', 'alors',
            'cependant', 'néanmoins', 'toutefois', 'pourtant', 'ainsi',
            'parce que', 'puisque', 'comme', 'quand', 'lorsque', 'si',
            'que', 'qui', 'dont', 'où', 'lequel', 'laquelle',
            'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
            'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs'
        }
    
    def reconstruct_sentences(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reconstruit des phrases complètes à partir des segments.
        
        Args:
            segments: Liste des segments Whisper originaux
            
        Returns:
            Liste de segments regroupés en phrases complètes
        """
        if not segments:
            return []
        
        reconstructed = []
        current_sentence = None
        
        for segment in segments:
            text = segment.get('text', '').strip()
            if not text:
                continue
            
            # Si pas de phrase en cours, commencer une nouvelle
            if current_sentence is None:
                current_sentence = self._init_sentence_from_segment(segment)
                continue
            
            # Décider si ce segment continue la phrase ou en commence une nouvelle
            if self._should_continue_sentence(current_sentence['text'], text):
                # Continuer la phrase actuelle
                current_sentence = self._merge_segments(current_sentence, segment)
            else:
                # Finaliser la phrase actuelle et en commencer une nouvelle
                reconstructed.append(current_sentence)
                current_sentence = self._init_sentence_from_segment(segment)
        
        # Ajouter la dernière phrase
        if current_sentence:
            reconstructed.append(current_sentence)
        
        # Post-traitement : réassigner les IDs et nettoyer
        return self._finalize_sentences(reconstructed)
    
    def _init_sentence_from_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Initialise une nouvelle phrase à partir d'un segment."""
        return {
            'id': segment.get('id', 0),
            'text': segment.get('text', '').strip(),
            'start': segment.get('start', 0.0),
            'end': segment.get('end', 0.0),
            'duration': segment.get('end', 0.0) - segment.get('start', 0.0),
            'speaker': segment.get('speaker', 'Inconnu'),
            'words': segment.get('words', []).copy() if segment.get('words') else [],
            'original_segments': [segment.get('id', 0)],  # Track des segments originaux
            'confidence': segment.get('confidence', 0.0) if 'confidence' in segment else None
        }
    
    def _should_continue_sentence(self, current_text: str, next_text: str) -> bool:
        """Détermine si le texte suivant continue la phrase actuelle."""
        current_text = current_text.strip()
        next_text = next_text.strip()
        
        if not current_text or not next_text:
            return False
        
        # Vérifier si la phrase précédente se termine réellement
        if self._is_complete_sentence(current_text):
            # Vérifier si le texte suivant commence par un mot de liaison
            first_word = next_text.split()[0].lower()
            if first_word in self.continuation_words:
                return True
            
            # Vérifier si c'est une continuation logique (minuscule au début)
            if next_text[0].islower():
                return True
            
            return False
        
        # Si la phrase précédente n'est pas complète, continuer
        return True
    
    def _is_complete_sentence(self, text: str) -> bool:
        """Vérifie si un texte forme une phrase complète."""
        text = text.strip()
        if not text:
            return False
        
        # Vérifier les marqueurs de fin
        if any(text.endswith(ending) for ending in self.sentence_endings):
            # Vérifier que ce n'est pas une fausse fin (abréviation, etc.)
            for pattern in self.continuation_patterns:
                if re.search(pattern + r'$', text, re.IGNORECASE):
                    return False
            return True
        
        return False
    
    def _merge_segments(self, current: Dict[str, Any], next_segment: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionne le segment suivant dans la phrase actuelle."""
        next_text = next_segment.get('text', '').strip()
        
        # Fusionner le texte
        if current['text'] and next_text:
            # Ajouter un espace si nécessaire
            if not current['text'].endswith((' ', '\n', '\t')):
                current['text'] += ' '
            current['text'] += next_text
        
        # Mettre à jour les timestamps
        current['end'] = next_segment.get('end', current['end'])
        current['duration'] = current['end'] - current['start']
        
        # Fusionner les mots si disponibles
        if next_segment.get('words'):
            if current['words'] is None:
                current['words'] = []
            current['words'].extend(next_segment['words'])
        
        # Garder trace des segments originaux
        current['original_segments'].append(next_segment.get('id', 0))
        
        # Conserver le même speaker (prendre le premier)
        # Si différent, on pourrait le noter mais gardons simple pour l'instant
        
        return current
    
    def _finalize_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Finalise les phrases reconstruites."""
        finalized = []
        
        for i, sentence in enumerate(sentences):
            # Réassigner les IDs
            sentence['id'] = i + 1
            
            # Nettoyer le texte
            sentence['text'] = self._clean_text(sentence['text'])
            
            # Recalculer la durée
            sentence['duration'] = sentence['end'] - sentence['start']
            
            # S'assurer que les mots sont cohérents avec le nouveau texte
            if sentence.get('words'):
                sentence['words'] = self._filter_words_by_timerange(
                    sentence['words'], 
                    sentence['start'], 
                    sentence['end']
                )
            
            finalized.append(sentence)
        
        return finalized
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte."""
        if not text:
            return ""
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Nettoyer les ponctuations doubles
        text = re.sub(r'[.]{2,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Espaces avant la ponctuation
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        return text.strip()
    
    def _filter_words_by_timerange(self, words: List[Dict], start: float, end: float) -> List[Dict]:
        """Filtre les mots pour qu'ils soient dans la plage temporelle."""
        if not words:
            return []
        
        filtered = []
        for word in words:
            word_start = word.get('start', 0)
            word_end = word.get('end', 0)
            
            # Garder le mot s'il chevauche avec la plage de la phrase
            if word_start <= end and word_end >= start:
                filtered.append(word)
        
        return filtered
    
    def get_reconstruction_stats(self, original_segments: List[Dict], reconstructed: List[Dict]) -> Dict[str, Any]:
        """Calcule des statistiques sur la reconstruction."""
        original_count = len(original_segments)
        reconstructed_count = len(reconstructed)
        
        # Calculer la réduction
        reduction_percent = ((original_count - reconstructed_count) / original_count) * 100
        
        # Analyser la distribution des longueurs
        original_lengths = [len(seg.get('text', '').split()) for seg in original_segments]
        reconstructed_lengths = [len(sent.get('text', '').split()) for sent in reconstructed]
        
        stats = {
            'original_segments': original_count,
            'reconstructed_sentences': reconstructed_count,
            'reduction_count': original_count - reconstructed_count,
            'reduction_percentage': round(reduction_percent, 1),
            'avg_words_original': round(sum(original_lengths) / len(original_lengths), 1) if original_lengths else 0,
            'avg_words_reconstructed': round(sum(reconstructed_lengths) / len(reconstructed_lengths), 1) if reconstructed_lengths else 0,
            'total_words': sum(reconstructed_lengths)
        }
        
        return stats