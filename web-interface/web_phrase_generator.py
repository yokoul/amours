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

# Import PyDub pour l'extraction des phrases individuelles
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print("⚠️ PyDub non disponible - extraction de phrases désactivée", file=sys.stderr)
    PYDUB_AVAILABLE = False

# Importer le sélecteur existant
try:
    # Import depuis phrase_montage.py
    sys.path.append(str(parent_dir / "examples"))
    from phrase_montage import PhraseSelector, PhraseMatch
    PHRASE_MONTAGE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Erreur import phrase_montage: {e}", file=sys.stderr)
    PHRASE_MONTAGE_AVAILABLE = False

# Pas besoin d'importer LoveTypeAnalyzer - les données sont dans les JSON

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
        
        # Pas besoin de LoveTypeAnalyzer - les données sont déjà dans les JSON
        self.love_analyzer = None
    
    def _generate_individual_phrase_files(self, phrases: List[PhraseMatch], 
                                         timestamp: str, 
                                         keywords: List[str],  # Liste complète des mots-clés
                                         include_next: int = 0) -> List[str]:
        """
        Génère les fichiers MP3 individuels pour chaque phrase
        
        Returns:
            Liste des URLs relatives des fichiers générés
        """
        if not PYDUB_AVAILABLE:
            return []
        
        individual_urls = []
        
        print(f"🎵 Génération de {len(phrases)} fichiers MP3 individuels...", file=sys.stderr)
        
        # Cache pour éviter de charger plusieurs fois le même fichier audio
        audio_cache = {}
        
        for i, phrase in enumerate(phrases, 1):
            try:
                # Charger l'audio source (avec cache)
                if phrase.audio_path not in audio_cache:
                    audio_cache[phrase.audio_path] = AudioSegment.from_file(phrase.audio_path)
                source_audio = audio_cache[phrase.audio_path]
                
                # Extraire la phrase
                start_ms = int(phrase.start * 1000)
                end_ms = int(phrase.end * 1000)
                
                # Ajouter padding
                padding_ms = 100
                start_ms = max(0, start_ms - padding_ms)
                
                # Étendre si include_next > 0
                if include_next > 0:
                    extended_end = self.selector._get_next_phrase_same_speaker(phrase, include_next)
                    if extended_end:
                        end_ms = int(extended_end * 1000)
                    else:
                        end_ms = min(len(source_audio), end_ms + padding_ms)
                else:
                    end_ms = min(len(source_audio), end_ms + padding_ms)
                
                phrase_audio = source_audio[start_ms:end_ms]
                
                # Normaliser
                phrase_audio = phrase_audio.normalize()
                
                # Appliquer des fondus doux
                fade_ms = 100
                phrase_audio = phrase_audio.fade_in(fade_ms).fade_out(fade_ms)
                
                # Nom du fichier avec le mot-clé de cette phrase
                # Utiliser le premier mot-clé trouvé dans cette phrase
                raw_keyword = phrase.keywords_found[0] if phrase.keywords_found else "extrait"
                # Nettoyer le mot-clé : garder uniquement la partie avant ≈ et enlever caractères spéciaux
                phrase_keyword = raw_keyword.split('≈')[0].strip()
                # Remplacer les caractères non-alphanumériques par underscore
                phrase_keyword = ''.join(c if c.isalnum() or c in '-_' else '_' for c in phrase_keyword)
                individual_filename = f"extrait_{phrase_keyword}_{i}_{timestamp}.mp3"
                individual_path = self.output_dir / individual_filename
                
                # Sauvegarder
                phrase_audio.export(str(individual_path), format="mp3", bitrate="192k")
                
                # URL relative
                individual_url = f"/audio/{individual_filename}"
                individual_urls.append(individual_url)
                
                print(f"  ✓ Phrase {i}: {individual_filename}", file=sys.stderr)
                
            except Exception as e:
                print(f"  ✗ Erreur phrase {i}: {e}", file=sys.stderr)
                individual_urls.append(None)
        
        return individual_urls
    
    def generate_web_phrases(self, keywords: List[str], num_phrases: int = 3, include_next: int = 0) -> WebPhraseResult:
        """
        Génère des phrases pour l'interface web
        
        Args:
            keywords: Liste des mots-clés
            num_phrases: Nombre de phrases à générer
            include_next: Nombre de phrases suivantes du même intervenant à inclure (0 = désactivé)
            
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
            # Rechercher une phrase pour chaque mot-clé
            selected_phrases = []
            
            for keyword in keywords:
                matches = self.selector.search_phrases(
                    [keyword],  # Chercher un seul mot-clé à la fois
                    max_results=5,  # Quelques options par mot
                    max_duration=15.0,
                    diversify_sources=True
                )
                
                if matches:
                    # Prendre la meilleure phrase pour ce mot-clé
                    selected_phrases.append(matches[0])
            
            if not selected_phrases:
                return WebPhraseResult(
                    success=False,
                    phrases=[],
                    error=f"Aucune phrase trouvée pour les mots: {', '.join(keywords)}"
                )
            
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
                keywords=keywords,
                include_next_phrases=include_next  # Inclure N phrases suivantes du même intervenant
            )
            
            # NOTE: Génération des MP3 individuels désactivée (génération à la demande)
            # Les fichiers seront générés uniquement quand l'utilisateur clique sur le bouton de téléchargement
            individual_files = []
            # if PYDUB_AVAILABLE:
            #     individual_files = self._generate_individual_phrase_files(
            #         selected_phrases, 
            #         timestamp, 
            #         keywords,  # Passer la liste complète des mots-clés
            #         include_next
            #     )
            
            # Calculer la durée totale (base)
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
            gap_duration = 1.0  # Même valeur que dans generate_phrase_montage
            
            # Calculer la position de début de chaque phrase dans le montage
            montage_time = 0.0
            
            for i, phrase in enumerate(selected_phrases):
                base_duration = phrase.end - phrase.start
                
                # Calculer la durée réelle qui inclut les extensions (include_next)
                real_duration = base_duration
                extended_end = phrase.end
                
                if include_next > 0:
                    # Utiliser la même méthode que le backend pour calculer l'extension
                    extended_end_calc = self.selector._get_next_phrase_same_speaker(phrase, include_next)
                    if extended_end_calc:
                        extended_end = extended_end_calc
                        real_duration = extended_end - phrase.start
                
                # Récupérer les timestamps mot par mot depuis les données de transcription
                # Inclure TOUS les mots entre phrase.start et extended_end (incluant les extensions)
                words_data = []
                if phrase.file_name in self.selector.transcription_data:
                    trans_data = self.selector.transcription_data[phrase.file_name]
                    segments = trans_data['transcription']['segments']
                    
                    # Calculer l'offset pour ajuster les timestamps au montage
                    offset = montage_time - phrase.start
                    
                    # Parcourir TOUS les segments pour trouver les mots dans l'intervalle [phrase.start, extended_end]
                    for seg in segments:
                        if 'words' in seg:
                            for word_obj in seg['words']:
                                word_start = word_obj['start']
                                word_end = word_obj['end']
                                
                                # Inclure tous les mots dans l'intervalle étendu
                                if word_start >= phrase.start and word_end <= extended_end:
                                    words_data.append({
                                        'word': word_obj['word'],
                                        'start': word_start + offset,  # Ajuster au temps du montage
                                        'end': word_end + offset       # Ajuster au temps du montage
                                    })
                
                
                # Construire le texte complet à partir des mots récupérés (incluant les extensions)
                full_text = ''.join([w['word'] for w in words_data]) if words_data else phrase.text
                
                # Ajouter l'URL du fichier MP3 individuel si disponible
                individual_audio_url = None
                if i < len(individual_files):
                    individual_audio_url = individual_files[i]
                
                phrases_data.append({
                    'index': i + 1,
                    'text': full_text,  # Texte complet incluant les extensions
                    'speaker': phrase.speaker,
                    'file_name': phrase.file_name,
                    'audio_path': phrase.audio_path,  # Chemin complet vers le fichier audio
                    'keywords_found': phrase.keywords_found,
                    'match_score': phrase.match_score,
                    'start_time': phrase.start,
                    'end_time': phrase.end,  # Fin de la phrase de base
                    'extended_end_time': extended_end,  # Fin étendue incluant les phrases suivantes
                    'duration': base_duration,  # Durée de base
                    'real_duration': real_duration,  # Durée réelle dans le montage (avec extensions)
                    'gap_after': gap_duration if i < len(selected_phrases) - 1 else 0,  # Gap après ce segment
                    'words': words_data,  # Timestamps mot par mot pour le karaoké
                    'love_type': getattr(phrase, 'love_type', None),
                    'love_analysis': getattr(phrase, 'love_analysis', None),  # Récupérer depuis le match
                    'individual_audio_url': individual_audio_url  # URL du MP3 individuel
                })
                
                # Avancer le temps du montage pour la prochaine phrase
                montage_time += real_duration
                if i < len(selected_phrases) - 1:
                    montage_time += gap_duration
            
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
            error="Usage: web_phrase_generator.py <num_phrases> <keyword1> [keyword2] ... [--include-next=<N>]"
        )
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return
    
    try:
        num_phrases = int(sys.argv[1])
        
        # Extraire include_next si présent
        include_next = 0
        keywords = []
        for arg in sys.argv[2:]:
            if arg.startswith('--include-next='):
                include_next = int(arg.split('=')[1])
            else:
                keywords.append(arg)
        
        generator = WebPhraseGenerator()
        result = generator.generate_web_phrases(keywords, num_phrases, include_next)
        
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