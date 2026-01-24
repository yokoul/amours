#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version web de phrase_montage.py
Génère des montages de phrases pour l'interface web sans lecture automatique
Retourne les informations au format JSON
"""

import sys
from pathlib import Path
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import base64

# Ajouter le répertoire parent au path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Importer le sélecteur existant
try:
    # Import depuis phrase_montage.py
    sys.path.append(str(parent_dir / "examples"))
    from phrase_montage import PhraseSelector, PhraseMatch
    PHRASE_MONTAGE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Erreur import phrase_montage: {e}", file=sys.stderr)
    PHRASE_MONTAGE_AVAILABLE = False

# Importer l'analyseur sémantique
try:
    sys.path.append(str(parent_dir / "src"))
    from love_analyzer import LoveTypeAnalyzer
    LOVE_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Analyseur sémantique non disponible: {e}", file=sys.stderr)
    LOVE_ANALYZER_AVAILABLE = False

@dataclass
class WebPhraseResult:
    """Résultat pour l'interface web"""
    success: bool
    phrases: List[Dict[str, Any]]
    audio_file: Optional[str] = None
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration_seconds: Optional[float] = None
    keywords: List[str] = None
    timestamp: str = None
    semantic_analysis: Optional[Dict[str, float]] = None  # Scores d'amour pour spidermap
    error: Optional[str] = None

class WebPhraseGenerator:
    """Générateur de phrases pour l'interface web"""
    
    def __init__(self, transcription_dir: str = "output_transcription", 
                 semantic_dir: str = "output_semantic",
                 output_dir: str = "web-interface/public/audio"):
        self.transcription_dir = Path(transcription_dir)
        self.semantic_dir = Path(semantic_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if PHRASE_MONTAGE_AVAILABLE:
            self.selector = PhraseSelector(
                transcription_dir=str(self.transcription_dir),
                semantic_dir=str(self.semantic_dir)
            )
        else:
            self.selector = None
        
        # Initialiser l'analyseur sémantique
        if LOVE_ANALYZER_AVAILABLE:
            self.love_analyzer = LoveTypeAnalyzer(
                use_semantic_analysis=True,
                reconstruct_sentences=False  # Pas besoin, on a déjà des phrases
            )
            print("✅ Analyseur sémantique initialisé", file=sys.stderr)
        else:
            self.love_analyzer = None
    
    def generate_web_phrases(self, keywords: List[str], num_phrases: int = 3) -> WebPhraseResult:
        """
        Génère des phrases pour l'interface web
        
        Args:
            keywords: Liste des mots-clés
            num_phrases: Nombre de phrases à générer
            
        Returns:
            WebPhraseResult avec toutes les infos pour l'interface
        """
        if not PHRASE_MONTAGE_AVAILABLE or not self.selector:
            return WebPhraseResult(
                success=False,
                phrases=[],
                error="Module phrase_montage non disponible"
            )
        
        try:
            # Rechercher les phrases avec tous les mots-clés
            matches = self.selector.search_phrases(
                keywords, 
                max_results=num_phrases * 5,  # Chercher plus pour avoir du choix
                max_duration=15.0,
                diversify_sources=True
            )
            
            if not matches:
                return WebPhraseResult(
                    success=False,
                    phrases=[],
                    error=f"Aucune phrase trouvée pour les mots: {', '.join(keywords)}"
                )
            
            # Sélection des meilleures phrases
            selected_phrases = matches[:num_phrases]
            
            # Créer le fichier audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = "_".join(keywords[:3])
            output_filename = f"web_montage_{keywords_str}_{num_phrases}phrases_{timestamp}.mp3"
            output_path = self.output_dir / output_filename
            
            # Générer le montage
            audio_file = self.selector.generate_phrase_montage(
                selected_phrases,
                str(output_path),
                gap_duration=1.0,  # Gap plus court pour le web
                fade_in_duration=0.1,
                fade_out_duration=0.1,
                normalize="rms",
                keywords=keywords
            )
            
            # Calculer la durée totale
            total_duration = sum(phrase.end - phrase.start for phrase in selected_phrases)
            total_duration += len(selected_phrases) * 1.0  # Gaps
            
            # URL relative pour l'interface web
            audio_url = f"/audio/{output_filename}"
            
            # Pour les petits fichiers seulement (< 100KB), encoder en base64
            audio_base64 = None
            if output_path.exists() and output_path.stat().st_size < 100 * 1024:  # < 100KB seulement
                try:
                    with open(output_path, 'rb') as f:
                        audio_data = f.read()
                        # Limiter strictement la taille
                        if len(audio_data) < 100 * 1024:
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                            print(f"🎵 Audio Base64 généré: {len(audio_base64)} chars", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️ Erreur encoding Base64: {e}", file=sys.stderr)
                    audio_base64 = None
            
            # Préparer les données des phrases
            phrases_data = []
            for i, phrase in enumerate(selected_phrases):
                phrases_data.append({
                    'index': i + 1,
                    'text': phrase.text,
                    'speaker': phrase.speaker,
                    'file_name': phrase.file_name,
                    'keywords_found': phrase.keywords_found,
                    'match_score': phrase.match_score,
                    'start_time': phrase.start,
                    'end_time': phrase.end,
                    'duration': phrase.end - phrase.start,
                    'love_type': getattr(phrase, 'love_type', None),
                    'love_analysis': getattr(phrase, 'love_analysis', None)  # Récupérer depuis le match
                })
            
            # Calculer l'analyse sémantique globale (moyenne des phrases)
            semantic_analysis = None
            love_analyses = [p.get('love_analysis') for p in phrases_data if p.get('love_analysis')]
            
            if love_analyses:
                # Calculer la moyenne des scores
                all_keys = set()
                for analysis in love_analyses:
                    all_keys.update(analysis.keys())
                
                semantic_analysis = {}
                for key in all_keys:
                    scores = [a.get(key, 0) for a in love_analyses if key in a]
                    if scores:
                        semantic_analysis[key] = sum(scores) / len(scores)
                
                print(f"🕷️ Analyse sémantique globale: {semantic_analysis}", file=sys.stderr)
            
            return WebPhraseResult(
                success=True,
                phrases=phrases_data,
                audio_file=str(output_path),
                audio_url=audio_url,
                audio_base64=audio_base64,
                duration_seconds=total_duration,
                keywords=keywords,
                timestamp=timestamp,
                semantic_analysis=semantic_analysis
            )
            
        except Exception as e:
            return WebPhraseResult(
                success=False,
                phrases=[],
                error=f"Erreur génération: {str(e)}"
            )
    
    def _deduplicate_matches(self, matches: List[PhraseMatch]) -> List[PhraseMatch]:
        """Déduplique les matches similaires"""
        unique_matches = []
        seen_texts = set()
        
        for match in matches:
            # Normaliser le texte pour détecter les doublons
            normalized_text = re.sub(r'\s+', ' ', match.text.lower().strip())
            
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_matches.append(match)
        
        return unique_matches
    
    def _select_best_phrases(self, matches: List[PhraseMatch], num_phrases: int, keywords: List[str]) -> List[PhraseMatch]:
        """Sélectionne les meilleures phrases avec diversité"""
        if len(matches) <= num_phrases:
            return matches
        
        # Trier par score de pertinence
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        selected = []
        used_speakers = set()
        used_files = set()
        
        # Première passe: privilégier la diversité des sources
        for match in matches:
            if len(selected) >= num_phrases:
                break
            
            # Éviter trop de phrases du même locuteur ou fichier
            speaker_count = sum(1 for s in selected if s.speaker == match.speaker)
            file_count = sum(1 for s in selected if s.file_name == match.file_name)
            
            if speaker_count < 2 and file_count < 2:
                selected.append(match)
            elif len(selected) < num_phrases // 2:  # Relaxer les contraintes si pas assez
                selected.append(match)
        
        # Deuxième passe: compléter avec les meilleurs restants
        for match in matches:
            if len(selected) >= num_phrases:
                break
            if match not in selected:
                selected.append(match)
        
        return selected[:num_phrases]

def main():
    """Point d'entrée pour l'interface web"""
    if len(sys.argv) < 3:
        result = WebPhraseResult(
            success=False,
            phrases=[],
            error="Usage: web_phrase_generator.py <num_phrases> <keyword1> [keyword2] ..."
        )
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return
    
    try:
        num_phrases = int(sys.argv[1])
        keywords = sys.argv[2:]
        
        generator = WebPhraseGenerator()
        result = generator.generate_web_phrases(keywords, num_phrases)
        
        # Sortie JSON pour Node.js avec encoding strict UTF-8
        result_json = json.dumps(asdict(result), ensure_ascii=False, indent=None, separators=(',', ':'))
        print(result_json.encode('utf-8').decode('utf-8'))
        
    except ValueError:
        result = WebPhraseResult(
            success=False,
            phrases=[],
            error="Le premier argument doit être un nombre"
        )
        result_json = json.dumps(asdict(result), ensure_ascii=False, indent=None, separators=(',', ':'))
        print(result_json.encode('utf-8').decode('utf-8'))
    except Exception as e:
        result = WebPhraseResult(
            success=False,
            phrases=[],
            error=f"Erreur inattendue: {str(e)}"
        )
        result_json = json.dumps(asdict(result), ensure_ascii=False, indent=None, separators=(',', ':'))
        print(result_json.encode('utf-8').decode('utf-8'))

if __name__ == "__main__":
    main()