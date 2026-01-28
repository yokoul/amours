#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de recherche dans les transcriptions
Recherche des mots-clés ou phrases dans les transcriptions et retourne les résultats avec contexte
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher

class TranscriptionSearcher:
    """Moteur de recherche pour les transcriptions audio"""
    
    def __init__(self, transcription_dir: str = "output_transcription"):
        self.transcription_dir = Path(transcription_dir)
        self.transcriptions = []
        self._load_transcriptions()
    
    def _load_transcriptions(self):
        """Charge tous les fichiers de transcription"""
        if not self.transcription_dir.exists():
            print(f"❌ Répertoire de transcription non trouvé: {self.transcription_dir}", file=sys.stderr)
            return
        
        json_files = list(self.transcription_dir.glob("*_with_speakers_complete.json"))
        print(f"📚 Chargement de {len(json_files)} fichiers de transcription...", file=sys.stderr)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.transcriptions.append({
                        'file': json_file.stem,
                        'path': str(json_file),
                        'data': data
                    })
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de {json_file}: {e}", file=sys.stderr)
    
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour la recherche (minuscules, sans accents pour comparaison flexible)"""
        # Garde les accents mais passe en minuscules pour la recherche
        return text.lower()
    
    def _count_sentences(self, text: str) -> int:
        """Compte approximativement le nombre de phrases dans un texte"""
        # Compter les ponctuations de fin de phrase
        sentence_endings = text.count('.') + text.count('!') + text.count('?')
        return max(1, sentence_endings)
    
    def _truncate_to_sentences(self, text: str, max_sentences: int) -> str:
        """Tronque un texte à un nombre maximum de phrases"""
        sentences = []
        current = []
        count = 0
        
        for char in text:
            current.append(char)
            if char in '.!?':
                count += 1
                if count >= max_sentences:
                    sentences.append(''.join(current))
                    break
                sentences.append(''.join(current))
                current = []
        
        result = ''.join(sentences).strip()
        if count > max_sentences:
            result += '...'
        return result
    
    def _get_segment_context(self, segments: List[Dict], target_index: int, max_sentences: int = 5) -> Dict[str, Any]:
        """
        Récupère le contexte autour d'un segment en limitant par nombre de phrases
        
        Args:
            segments: Liste de tous les segments
            target_index: Index du segment trouvé
            max_sentences: Nombre maximum de phrases dans le contexte (défaut: 5)
        
        Returns:
            Dictionnaire avec les segments de contexte
        """
        context_segments = []
        total_sentences = 0
        
        # Toujours inclure le segment cible
        target_seg = segments[target_index]
        target_sentences = self._count_sentences(target_seg['text'])
        context_segments.append(target_seg)
        total_sentences = target_sentences
        
        # Si le segment cible dépasse déjà la limite, le tronquer
        if total_sentences > max_sentences:
            # Tronquer le texte au nombre maximum de phrases
            truncated_text = self._truncate_to_sentences(target_seg['text'], max_sentences)
            return {
                'segments': [{'text': truncated_text, **{k: v for k, v in target_seg.items() if k != 'text'}}],
                'start_time': target_seg['start'],
                'end_time': target_seg['end'],
                'duration': target_seg['end'] - target_seg['start'],
                'text': truncated_text,
                'target_segment_index': target_index,
                'total_sentences': max_sentences
            }
        
        # Ajouter des segments avant et après tant qu'on ne dépasse pas max_sentences
        before_idx = target_index - 1
        after_idx = target_index + 1
        
        # Alterner entre avant et après pour équilibrer le contexte
        while (before_idx >= 0 or after_idx < len(segments)) and total_sentences < max_sentences:
            # Essayer d'ajouter un segment avant
            if before_idx >= 0:
                seg = segments[before_idx]
                seg_sentences = self._count_sentences(seg['text'])
                if total_sentences + seg_sentences <= max_sentences:
                    context_segments.insert(0, seg)
                    total_sentences += seg_sentences
                    before_idx -= 1
                else:
                    # On ne peut plus ajouter avant sans dépasser
                    before_idx = -1
            
            # Essayer d'ajouter un segment après
            if after_idx < len(segments) and total_sentences < max_sentences:
                seg = segments[after_idx]
                seg_sentences = self._count_sentences(seg['text'])
                if total_sentences + seg_sentences <= max_sentences:
                    context_segments.append(seg)
                    total_sentences += seg_sentences
                    after_idx += 1
                else:
                    # On ne peut plus ajouter après sans dépasser
                    after_idx = len(segments)
        
        # Construire le texte complet du contexte
        full_text = " ".join([seg['text'] for seg in context_segments])
        
        # Calculer les timecodes de début et fin
        start_time = context_segments[0]['start']
        end_time = context_segments[-1]['end']
        
        return {
            'segments': context_segments,
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'text': full_text,
            'target_segment_index': target_index,
            'total_sentences': total_sentences
        }
    
    def _search_in_segments(self, segments: List[Dict], query: str) -> List[int]:
        """
        Recherche les segments contenant la requête
        
        Returns:
            Liste des indices des segments correspondants
        """
        query_normalized = self._normalize_text(query)
        matching_indices = []
        
        for idx, segment in enumerate(segments):
            segment_text = self._normalize_text(segment.get('text', ''))
            
            # Recherche simple: le texte contient-il la requête ?
            if query_normalized in segment_text:
                matching_indices.append(idx)
        
        return matching_indices
    
    def _calculate_relevance_score(self, segment_text: str, query: str) -> float:
        """
        Calcule un score de pertinence pour le tri des résultats
        Plus le score est élevé, plus le résultat est pertinent
        """
        segment_lower = self._normalize_text(segment_text)
        query_lower = self._normalize_text(query)
        
        # Score de base: ratio de similarité
        score = SequenceMatcher(None, segment_lower, query_lower).ratio()
        
        # Bonus si la requête exacte est présente
        if query_lower in segment_lower:
            score += 0.5
        
        # Bonus si c'est au début du segment
        if segment_lower.startswith(query_lower):
            score += 0.3
        
        return score
    
    def search(self, query: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Recherche principale
        
        Args:
            query: Texte à rechercher (mots-clés ou phrase)
            max_results: Nombre maximum de résultats à retourner
        
        Returns:
            Dictionnaire avec les résultats de recherche
        """
        if not query or len(query.strip()) < 2:
            return {
                'success': False,
                'error': 'La requête doit contenir au moins 2 caractères',
                'results': []
            }
        
        query = query.strip()
        print(f"🔍 Recherche de: '{query}'", file=sys.stderr)
        
        all_results = []
        
        # Parcourir toutes les transcriptions
        for trans in self.transcriptions:
            data = trans['data']
            segments = data.get('transcription', {}).get('segments', [])
            
            if not segments:
                continue
            
            # Rechercher dans les segments
            matching_indices = self._search_in_segments(segments, query)
            
            # Pour chaque correspondance, créer un résultat avec contexte
            for idx in matching_indices:
                context = self._get_segment_context(segments, idx, max_sentences=5)
                
                # Récupérer les métadonnées du fichier source
                metadata = data.get('metadata', {})
                audio_file = metadata.get('file', 'unknown')
                audio_path = metadata.get('path', '')
                
                # Calculer le score de pertinence
                relevance = self._calculate_relevance_score(segments[idx]['text'], query)
                
                result = {
                    'source_file': audio_file,
                    'source_path': audio_path,
                    'transcription_file': trans['file'],
                    'segment_id': segments[idx].get('id', idx),
                    'speaker': segments[idx].get('speaker', 'Unknown'),
                    'start_time': context['start_time'],
                    'end_time': context['end_time'],
                    'duration': context['duration'],
                    'matched_text': segments[idx]['text'],
                    'context_text': context['text'],
                    'context_segments': context['segments'],
                    'relevance_score': relevance
                }
                
                all_results.append(result)
        
        # Trier par pertinence décroissante
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Limiter le nombre de résultats
        results = all_results[:max_results]
        
        print(f"✅ Trouvé {len(all_results)} résultats (retournant {len(results)})", file=sys.stderr)
        
        return {
            'success': True,
            'query': query,
            'total_results': len(all_results),
            'returned_results': len(results),
            'results': results
        }

def main():
    """Point d'entrée pour l'interface web"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: search_transcriptions.py <query> [max_results]'
        }))
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    # Déterminer le chemin du répertoire de transcription
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    transcription_dir = project_root / "output_transcription"
    
    # Créer le moteur de recherche
    searcher = TranscriptionSearcher(str(transcription_dir))
    
    # Effectuer la recherche
    results = searcher.search(query, max_results)
    
    # Retourner les résultats en JSON
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
