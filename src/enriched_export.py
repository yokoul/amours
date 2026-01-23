"""
Gestionnaire d'export enrichi avec analyses d'amour.
Étend ExportManager avec des fonctionnalités d'analyse sémantique.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

from export import ExportManager
from love_analyzer import LoveTypeAnalyzer


class EnrichedExportManager(ExportManager):
    """Gestionnaire d'export avec analyse d'amour intégrée."""
    
    def __init__(self):
        """Initialise le gestionnaire enrichi."""
        super().__init__()
        self.love_analyzer = LoveTypeAnalyzer()
    
    def export_with_love_analysis(
        self, 
        transcription_data: Dict[str, Any], 
        output_path: str,
        formats: List[str] = None
    ) -> Dict[str, Any]:
        """
        Exporte avec analyse d'amour complète.
        
        Args:
            transcription_data: Données de transcription
            output_path: Chemin de base pour les fichiers
            formats: Liste des formats à générer ['json', 'csv', 'artistic', 'srt', 'summary']
            
        Returns:
            Données enrichies avec l'analyse d'amour
        """
        if formats is None:
            formats = ['json', 'csv', 'artistic', 'srt', 'summary']
        
        # Analyser les types d'amour
        enriched_data = self.love_analyzer.analyze_transcription(transcription_data)
        
        output_base = Path(output_path).with_suffix('')
        
        # JSON complet avec analyse
        if 'json' in formats:
            json_path = f"{output_base}_love_analysis.json"
            self.export_json(enriched_data, json_path)
        
        # CSV enrichi
        if 'csv' in formats:
            csv_path = f"{output_base}_love_data.csv"
            self.export_love_csv(enriched_data, csv_path)
        
        # Format artistique avec amour
        if 'artistic' in formats:
            artistic_path = f"{output_base}_love_artistic.json"
            self.export_love_artistic_format(enriched_data, artistic_path)
        
        # Sous-titres avec types d'amour
        if 'srt' in formats:
            srt_path = f"{output_base}_love_subtitles.srt"
            self.export_love_srt_subtitles(enriched_data, srt_path)
        
        # Résumé d'analyse
        if 'summary' in formats:
            summary_path = f"{output_base}_love_summary.txt"
            self.export_love_summary(enriched_data, summary_path)
        
        return enriched_data
    
    def export_love_csv(self, enriched_data: Dict[str, Any], output_path: str) -> None:
        """Exporte CSV avec colonnes d'analyse d'amour."""
        try:
            output_file = Path(output_path)
            if output_file.suffix.lower() != '.csv':
                output_file = output_file.with_suffix('.csv')
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Préparer les données
            rows = []
            metadata = enriched_data["metadata"]
            love_categories = list(enriched_data["transcription"]["segments"][0]["love_analysis"].keys())
            
            for segment in enriched_data["transcription"]["segments"]:
                segment_id = segment["id"]
                segment_start = segment["start"]
                segment_end = segment["end"]
                segment_text = segment["text"]
                segment_speaker = segment.get("speaker", "Inconnu")
                love_scores = segment["love_analysis"]
                dominant_love = segment.get("dominant_love_type", "neutre")
                love_confidence = segment.get("love_confidence", 0.0)
                
                if segment.get("words"):
                    # Une ligne par mot avec analyse d'amour
                    for word_idx, word in enumerate(segment["words"]):
                        row = {
                            # Métadonnées de base
                            "file_name": metadata["file"],
                            "transcription_date": metadata["transcription_date"],
                            
                            # Informations du segment
                            "segment_id": segment_id,
                            "segment_start": segment_start,
                            "segment_end": segment_end,
                            "segment_text": segment_text,
                            "segment_speaker": segment_speaker,
                            
                            # Informations du mot
                            "word_index": word_idx,
                            "word": word["word"],
                            "word_start": word["start"],
                            "word_end": word["end"],
                            "word_confidence": word.get("confidence", 0.0),
                            "word_speaker": word.get("speaker", segment_speaker),
                            
                            # Analyse d'amour (au niveau du segment)
                            "dominant_love_type": dominant_love,
                            "love_confidence": love_confidence,
                        }
                        
                        # Ajouter chaque score d'amour comme colonne
                        for love_type, score in love_scores.items():
                            row[f"love_{love_type}"] = score
                        
                        rows.append(row)
                else:
                    # Segment sans mots détaillés
                    row = {
                        "file_name": metadata["file"],
                        "transcription_date": metadata["transcription_date"],
                        "segment_id": segment_id,
                        "segment_start": segment_start,
                        "segment_end": segment_end,
                        "segment_text": segment_text,
                        "segment_speaker": segment_speaker,
                        "word_index": 0,
                        "word": segment_text,
                        "word_start": segment_start,
                        "word_end": segment_end,
                        "word_confidence": 0.0,
                        "word_speaker": segment_speaker,
                        "dominant_love_type": dominant_love,
                        "love_confidence": love_confidence,
                    }
                    
                    for love_type, score in love_scores.items():
                        row[f"love_{love_type}"] = score
                    
                    rows.append(row)
            
            # Créer et sauvegarder le DataFrame
            df = pd.DataFrame(rows)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"📊 CSV avec analyse d'amour : {output_file.name}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur export CSV amour : {str(e)}")
    
    def export_love_artistic_format(self, enriched_data: Dict[str, Any], output_path: str) -> None:
        """Exporte format artistique enrichi avec analyse d'amour."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Format artistique avec analyses d'amour
            artistic_data = {
                "project_info": {
                    "source_file": enriched_data["metadata"]["file"],
                    "total_duration": enriched_data["metadata"]["duration"],
                    "created_at": datetime.now().isoformat(),
                    "analysis_type": "love_semantic_analysis",
                    "full_text": enriched_data["transcription"]["text"]
                },
                
                "love_timeline": [],
                "love_vocabulary": {},
                "love_statistics": enriched_data["love_analysis"]["statistics_by_type"],
                "love_summary": enriched_data["love_analysis"],
                
                "artistic_segments": [],
                "dominant_emotions": {}
            }
            
            # Timeline enrichie avec types d'amour
            for segment in enriched_data["transcription"]["segments"]:
                love_scores = segment["love_analysis"]
                dominant_type = segment.get("dominant_love_type", "neutre")
                
                timeline_entry = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "speaker": segment.get("speaker", "Inconnu"),
                    "love_type": dominant_type,
                    "love_confidence": segment.get("love_confidence", 0.0),
                    "love_scores": love_scores
                }
                
                artistic_data["love_timeline"].append(timeline_entry)
                
                # Segments artistiques (scores élevés)
                if segment.get("love_confidence", 0) > 0.3:
                    artistic_data["artistic_segments"].append({
                        "timestamp": segment["start"],
                        "duration": segment["duration"],
                        "text": segment["text"],
                        "love_type": dominant_type,
                        "intensity": segment["love_confidence"],
                        "speaker": segment.get("speaker", "Inconnu")
                    })
            
            # Vocabulaire d'amour unique
            love_words = defaultdict(int)
            for segment in enriched_data["transcription"]["segments"]:
                if segment.get("love_confidence", 0) > 0.1:
                    words = segment["text"].lower().split()
                    for word in words:
                        # Filtrer les mots liés à l'amour
                        if any(keyword in word for keywords in self.love_analyzer.love_categories.values() 
                              for keyword in keywords["keywords"]):
                            love_words[word] += 1
            
            artistic_data["love_vocabulary"] = dict(love_words)
            
            # Émotions dominantes par période
            time_segments = self._create_time_segments(enriched_data, segment_duration=30)  # 30s
            artistic_data["dominant_emotions"] = time_segments
            
            # Sauvegarder
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(artistic_data, f, ensure_ascii=False, indent=2)
            
            print(f"🎨 Format artistique avec amour : {output_file.name}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur export artistique amour : {str(e)}")
    
    def export_love_srt_subtitles(self, enriched_data: Dict[str, Any], output_path: str) -> None:
        """Exporte SRT avec types d'amour et intervenants."""
        try:
            output_file = Path(output_path)
            if output_file.suffix.lower() != '.srt':
                output_file = output_file.with_suffix('.srt')
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            def format_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(enriched_data["transcription"]["segments"], 1):
                    start_time = format_time(segment["start"])
                    end_time = format_time(segment["end"])
                    text = segment["text"].strip()
                    speaker = segment.get("speaker", "")
                    love_type = segment.get("dominant_love_type", "")
                    love_confidence = segment.get("love_confidence", 0.0)
                    
                    # Construire le texte enrichi
                    enriched_text = text
                    
                    # Ajouter l'intervenant
                    if speaker and speaker != "Inconnu":
                        enriched_text = f"[{speaker}] {enriched_text}"
                    
                    # Ajouter le type d'amour si significatif
                    if love_type != "neutre" and love_confidence > 0.2:
                        love_emoji = self._get_love_emoji(love_type)
                        enriched_text = f"{enriched_text} {love_emoji}{love_type.title()}"
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{enriched_text}\n\n")
            
            print(f"📺 Sous-titres enrichis : {output_file.name}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur export SRT amour : {str(e)}")
    
    def export_love_summary(self, enriched_data: Dict[str, Any], output_path: str) -> None:
        """Exporte un résumé textuel de l'analyse d'amour."""
        try:
            output_file = Path(output_path)
            if output_file.suffix.lower() != '.txt':
                output_file = output_file.with_suffix('.txt')
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            summary = self.love_analyzer.get_love_summary(enriched_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
                f.write("\n\n" + "=" * 60 + "\n")
                f.write("SEGMENTS LES PLUS REPRÉSENTATIFS PAR TYPE\n")
                f.write("=" * 60 + "\n\n")
                
                # Ajouter les segments représentatifs
                stats = enriched_data["love_analysis"]["statistics_by_type"]
                for love_type, data in stats.items():
                    if data["representative_segments"]:
                        f.write(f"🔥 {love_type.upper()} :\n")
                        for segment in data["representative_segments"]:
                            f.write(f"   • Score {segment['score']:.3f} - \"{segment['text']}\"\n")
                            f.write(f"     Timestamp: {segment['start']:.1f}s - {segment['end']:.1f}s\n\n")
            
            print(f"📄 Résumé d'analyse : {output_file.name}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur export résumé : {str(e)}")
    
    def _get_love_emoji(self, love_type: str) -> str:
        """Retourne un emoji approprié pour le type d'amour."""
        emoji_map = {
            "romantique": "💕",
            "familial": "👨‍👩‍👧‍👦",
            "amical": "🤝",
            "erotique": "🔥",
            "compassionnel": "💝",
            "narcissique": "🪞",
            "platonique": "✨"
        }
        return emoji_map.get(love_type, "💖")
    
    def _create_time_segments(self, enriched_data: Dict[str, Any], segment_duration: float = 30.0) -> Dict:
        """Crée des segments temporels pour l'analyse artistique."""
        total_duration = enriched_data["metadata"]["duration"]
        time_segments = {}
        
        current_time = 0.0
        segment_index = 0
        
        while current_time < total_duration:
            end_time = min(current_time + segment_duration, total_duration)
            
            # Trouver les segments dans cette période
            period_segments = []
            for segment in enriched_data["transcription"]["segments"]:
                if segment["start"] >= current_time and segment["start"] < end_time:
                    period_segments.append(segment)
            
            if period_segments:
                # Calculer l'émotion dominante pour cette période
                love_scores = defaultdict(list)
                for seg in period_segments:
                    for love_type, score in seg["love_analysis"].items():
                        love_scores[love_type].append(score)
                
                # Moyenne des scores
                avg_scores = {}
                for love_type, scores in love_scores.items():
                    avg_scores[love_type] = sum(scores) / len(scores) if scores else 0
                
                dominant_emotion = max(avg_scores, key=avg_scores.get) if avg_scores else "neutre"
                
                time_segments[f"period_{segment_index}"] = {
                    "start": current_time,
                    "end": end_time,
                    "dominant_emotion": dominant_emotion,
                    "emotion_score": avg_scores.get(dominant_emotion, 0),
                    "all_scores": avg_scores,
                    "segments_count": len(period_segments)
                }
            
            current_time = end_time
            segment_index += 1
        
        return time_segments