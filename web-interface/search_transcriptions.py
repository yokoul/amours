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
    
    def _get_segment_context(self, segments: List[Dict], target_index: int, context_size: int = 2) -> Dict[str, Any]:
        """
        Récupère le contexte autour d'un segment (segments avant et après)
        
        Args:
            segments: Liste de tous les segments
            target_index: Index du segment trouvé
            context_size: Nombre de segments avant/après à inclure (défaut: 2-3)
        
        Returns:
            Dictionnaire avec les segments de contexte
        """
        start_idx = max(0, target_index - context_size)
        end_idx = min(len(segments), target_index + context_size + 1)
        
        context_segments = segments[start_idx:end_idx]
        
        # Calculer les timecodes de début et fin
        start_time = context_segments[0]['start']
        end_time = context_segments[-1]['end']
        
        # Construire le texte complet du contexte
        context_text = " ".join([seg['text'] for seg in context_segments])
        
        return {
            'segments': context_segments,
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'text': context_text,
            'target_segment_index': target_index,
            'context_start_index': start_idx,
            'context_end_index': end_idx
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
                context = self._get_segment_context(segments, idx, context_size=2)
                
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
