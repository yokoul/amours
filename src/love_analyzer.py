"""
Analyseur sémantique pour la catégorisation des types d'amour.
Utilise des modèles de traitement du langage naturel et des règles lexicales.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from scipy.spatial.distance import cosine
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sentence_reconstructor import SentenceReconstructor
    SENTENCE_RECONSTRUCTOR_AVAILABLE = True
except ImportError:
    SENTENCE_RECONSTRUCTOR_AVAILABLE = False


def convert_numpy_types(obj):
    """Convertit récursivement tous les types NumPy en types Python standards."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class LoveTypeAnalyzer:
    """Analyseur des types d'amour dans les segments de texte."""
    
    def __init__(self, min_score_threshold=0.1, use_semantic_analysis=True, reconstruct_sentences=True):
        """
        Initialise l'analyseur.
        
        Args:
            min_score_threshold: Seuil minimum pour considérer un score d'amour significatif
            use_semantic_analysis: Utiliser l'analyse sémantique avec sentence-transformers
            reconstruct_sentences: Reconstruire les phrases complètes avant analyse
        """
        self.min_score_threshold = min_score_threshold
        self.use_semantic_analysis = use_semantic_analysis
        self.reconstruct_sentences = reconstruct_sentences
        self.semantic_model = None
        self.love_embeddings = None
        self.sentence_reconstructor = None
        
        # Initialiser le reconstructeur de phrases si demandé
        if self.reconstruct_sentences and SENTENCE_RECONSTRUCTOR_AVAILABLE:
            self.sentence_reconstructor = SentenceReconstructor()
            print("✅ Reconstructeur de phrases initialisé")
        
        # Initialiser le modèle sémantique
        self._init_semantic_model()
        
        self.love_categories = {
            "romantique": {
                "description": "Amour passionnel, romantique et idéalisé",
                "keywords": [
                    "romantique", "passion", "séduction", "charme", "beauté", "rêve",
                    "idéal", "parfait", "merveilleux", "magique", "enchanteur",
                    "coup de foudre", "âme sœur", "prince", "princesse", "conte de fées",
                    "étincelle", "chemistry", "attraction", "fascination"
                ],
                "patterns": [
                    r"coup de foudre",
                    r"âme[s]?\s+sœur[s]?",
                    r"amour.*rêve",
                    r"romantique",
                    r"passion.*amour",
                    r"séduire|séduction"
                ]
            },
            
            "familial": {
                "description": "Amour familial, parental, fraternel",
                "keywords": [
                    "famille", "parents", "maman", "papa", "enfant", "fils", "fille",
                    "frère", "sœur", "grand-mère", "grand-père", "oncle", "tante",
                    "protection", "sécurité", "tendresse", "douceur", "bienveillance",
                    "maternel", "paternel", "fraternal", "filial", "foyer", "maison",
                    "éducation", "élever", "grandir"
                ],
                "patterns": [
                    r"amour.*famille",
                    r"amour.*parents?",
                    r"maternel|paternel",
                    r"famille.*amour",
                    r"enfants?.*amour",
                    r"protection.*amour"
                ]
            },
            
            "amical": {
                "description": "Amour amical, camaraderie, amitié profonde",
                "keywords": [
                    "ami", "amitié", "copain", "copine", "camarade", "compagnon",
                    "solidarité", "loyauté", "fidélité", "confiance", "partage",
                    "complicité", "entraide", "soutien", "fraternité", "communion",
                    "équipe", "groupe", "communauté", "ensemble"
                ],
                "patterns": [
                    r"amitié.*amour",
                    r"amour.*ami[es]?",
                    r"fraternité",
                    r"solidarité.*amour",
                    r"amis?.*amour"
                ]
            },
            
            "erotique": {
                "description": "Amour sensuel, physique, charnel",
                "keywords": [
                    "désir", "plaisir", "sensuel", "charnel", "physique", "corps",
                    "peau", "caresse", "baiser", "embrasser", "toucher", "sensation",
                    "volupté", "extase", "orgasme", "intimité", "nu", "nudité",
                    "sexe", "sexuel", "érotique", "libido", "pulsion"
                ],
                "patterns": [
                    r"désir.*amour",
                    r"amour.*physique",
                    r"sensuel.*amour",
                    r"plaisir.*amour",
                    r"corps.*amour",
                    r"charnel"
                ]
            },
            
            "compassionnel": {
                "description": "Amour altruiste, compassionnel, universel",
                "keywords": [
                    "compassion", "empathie", "altruisme", "humanité", "universel",
                    "bienveillance", "générosité", "don", "sacrifice", "service",
                    "aide", "soin", "guérison", "pardon", "réconciliation",
                    "paix", "harmonie", "spirituel", "divin", "sacré"
                ],
                "patterns": [
                    r"amour.*humanité",
                    r"amour.*universel",
                    r"compassion.*amour",
                    r"altruisme",
                    r"amour.*spirituel"
                ]
            },
            
            "narcissique": {
                "description": "Amour de soi, égocentrique, possessif",
                "keywords": [
                    "moi", "je", "mon", "ma", "mes", "possession", "appartenir",
                    "jalousie", "envie", "contrôle", "dominer", "pouvoir",
                    "égoïsme", "narcissisme", "orgueil", "vanité", "fierté",
                    "mérite", "droit", "exiger", "avoir besoin"
                ],
                "patterns": [
                    r"mon.*amour",
                    r"m'appartien[ts]",
                    r"jalou[sx].*amour",
                    r"posséd[er].*amour",
                    r"contrôl[er].*amour"
                ]
            },
            
            "platonique": {
                "description": "Amour idéalisé, spirituel, sans dimension physique",
                "keywords": [
                    "idéal", "parfait", "pur", "innocent", "spirituel", "âme",
                    "esprit", "pensée", "admiration", "respect", "vénération",
                    "platonique", "chaste", "sublime", "élevé", "noble",
                    "inspiration", "muse", "art", "beauté", "esthétique"
                ],
                "patterns": [
                    r"amour.*pur",
                    r"amour.*platonique",
                    r"amour.*spirituel",
                    r"amour.*idéal",
                    r"admiration.*amour"
                ]
            }
        }
        
        # Initialiser les outils d'analyse
        self.sentiment_analyzer = None
        self.tfidf_vectorizer = None
        self._init_analyzers()
        
        # Créer les embeddings des types d'amour si possible
        if self.use_semantic_analysis and self.semantic_model:
            self._create_love_embeddings()
    
    def _init_semantic_model(self):
        """Initialise le modèle sentence-transformers."""
        if not self.use_semantic_analysis or not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️  Analyse sémantique désactivée ou sentence-transformers non disponible")
            return
        
        try:
            # Prioriser le modèle multilingue pour le français
            model_options = [
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "sentence-transformers/all-MiniLM-L12-v2",
                "paraphrase-multilingual-MiniLM-L12-v2",
                "all-MiniLM-L12-v2"
            ]
            
            for model_name in model_options:
                try:
                    print(f"🤖 Chargement du modèle sémantique : {model_name}")
                    self.semantic_model = SentenceTransformer(model_name)
                    print(f"✅ Modèle chargé : {model_name}")
                    break
                except Exception as e:
                    print(f"⚠️  Échec du chargement de {model_name}: {str(e)}")
                    continue
            
            if not self.semantic_model:
                print("❌ Aucun modèle sentence-transformers disponible")
                self.use_semantic_analysis = False
                
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du modèle sémantique : {str(e)}")
            self.use_semantic_analysis = False
    
    def _create_love_embeddings(self):
        """Crée les embeddings des descriptions des types d'amour."""
        if not self.semantic_model:
            return
        
        try:
            # Créer des descriptions enrichies pour chaque type d'amour
            love_descriptions = {}
            for love_type, info in self.love_categories.items():
                # Combiner description + mots-clés principaux
                description = info["description"]
                key_keywords = " ".join(info["keywords"][:10])  # Top 10 des mots-clés
                full_description = f"{description}. Mots-clés : {key_keywords}"
                love_descriptions[love_type] = full_description
            
            # Générer les embeddings
            descriptions_list = list(love_descriptions.values())
            embeddings = self.semantic_model.encode(descriptions_list)
            
            # Stocker avec les noms des types
            self.love_embeddings = {}
            for i, love_type in enumerate(love_descriptions.keys()):
                self.love_embeddings[love_type] = embeddings[i]
            
            print(f"✅ Embeddings créés pour {len(self.love_embeddings)} types d'amour")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des embeddings : {str(e)}")
            self.love_embeddings = None
    
    def _init_analyzers(self):
        """Initialise les outils d'analyse."""
        if TRANSFORMERS_AVAILABLE:
            try:
                # Utiliser un modèle français pour l'analyse de sentiment
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="nlptown/bert-base-multilingual-uncased-sentiment",
                    device=-1  # CPU pour éviter les problèmes GPU
                )
                print("✅ Analyseur de sentiment chargé")
            except Exception as e:
                print(f"⚠️  Erreur chargement analyseur : {e}")
        
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words=self._get_french_stopwords(),
                ngram_range=(1, 2),
                max_features=1000
            )
            print("✅ Vectoriseur TF-IDF initialisé")
    
    def _get_french_stopwords(self) -> List[str]:
        """Retourne une liste de mots vides français."""
        return [
            'le', 'de', 'un', 'à', 'être', 'et', 'en', 'avoir', 'que', 'pour',
            'dans', 'ce', 'il', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout',
            'plus', 'par', 'grand', 'ou', 'si', 'les', 'du', 'comme', 'mon',
            'des', 'au', 'nous', 'vous', 'ça', 'été', 'cette', 'son', 'sa'
        ]
    
    def analyze_segment(self, text: str) -> Dict[str, float]:
        """
        Analyse un segment de texte et retourne les scores d'amour.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire avec les scores pour chaque type d'amour (0-1)
        """
        text_lower = text.lower()
        scores = {}
        
        for love_type, category_data in self.love_categories.items():
            # Score traditionnel (mots-clés + regex)
            traditional_score = self._calculate_love_score(text_lower, category_data)
            
            # Score sémantique si disponible
            semantic_score = 0.0
            if self.use_semantic_analysis and self.semantic_model and self.love_embeddings:
                semantic_score = self._calculate_semantic_score(text, love_type)
            
            # Combiner les scores (pondération adaptative)
            if semantic_score > 0:
                # Si on a l'analyse sémantique, donner plus de poids
                final_score = (traditional_score * 0.4) + (semantic_score * 0.6)
            else:
                # Sinon, utiliser seulement l'analyse traditionnelle
                final_score = traditional_score
            
            # S’assurer que c'est un float Python standard
            scores[love_type] = float(round(final_score, 3))
        
        return scores
    
    def _calculate_semantic_score(self, text: str, love_type: str) -> float:
        """Calcule le score sémantique pour un type d'amour donné."""
        try:
            if not self.semantic_model or not self.love_embeddings or love_type not in self.love_embeddings:
                return 0.0
            
            # Générer l'embedding du texte
            text_embedding = self.semantic_model.encode([text])
            love_embedding = self.love_embeddings[love_type]
            
            # Calculer la similarité cosinus
            similarity = 1 - cosine(text_embedding[0], love_embedding)
            
            # Normaliser et ajuster le score (convertir en float Python)
            # Les embeddings peuvent donner des scores assez bas, donc on les amplifie
            semantic_score = float(max(0.0, min(1.0, similarity * 1.5)))
            
            return semantic_score
            
        except Exception as e:
            print(f"⚠️  Erreur calcul sémantique pour {love_type}: {str(e)}")
            return 0.0
    
    def _calculate_love_score(self, text: str, category_data: Dict) -> float:
        """Calcule le score d'un type d'amour spécifique."""
        score = 0.0
        text_words = text.split()
        
        # Score basé sur les mots-clés
        keyword_score = 0
        for keyword in category_data["keywords"]:
            if keyword.lower() in text:
                # Score plus élevé pour les mots exacts
                if keyword.lower() in text_words:
                    keyword_score += 2.0
                else:
                    keyword_score += 1.0
        
        # Normaliser le score des mots-clés
        if len(category_data["keywords"]) > 0:
            keyword_score = min(1.0, keyword_score / len(category_data["keywords"]) * 10)
        
        # Score basé sur les patterns regex
        pattern_score = 0
        for pattern in category_data.get("patterns", []):
            if re.search(pattern, text, re.IGNORECASE):
                pattern_score += 0.3
        
        pattern_score = min(0.5, pattern_score)
        
        # Bonus si le mot "amour" est présent
        love_bonus = 0.1 if "amour" in text else 0
        
        # Score final
        score = keyword_score * 0.7 + pattern_score * 0.2 + love_bonus * 0.1
        
        return min(1.0, score)
    
    def analyze_transcription(self, transcription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse une transcription complète et ajoute les catégories d'amour.
        
        Args:
            transcription_data: Données de transcription complètes
            
        Returns:
            Données enrichies avec les analyses d'amour
        """
        print("💝 Analyse sémantique des types d'amour...")
        
        enriched_data = transcription_data.copy()
        original_segments = enriched_data["transcription"]["segments"]
        
        # Reconstruction des phrases complètes si activée
        if self.reconstruct_sentences and self.sentence_reconstructor:
            print("🔧 Reconstruction des phrases complètes...")
            reconstructed_segments = self.sentence_reconstructor.reconstruct_sentences(original_segments)
            
            # Calculer et afficher les statistiques de reconstruction
            stats = self.sentence_reconstructor.get_reconstruction_stats(original_segments, reconstructed_segments)
            print(f"   📊 {stats['original_segments']} segments → {stats['reconstructed_sentences']} phrases")
            print(f"   📉 Réduction: {stats['reduction_count']} segments (-{stats['reduction_percentage']}%)")
            print(f"   📝 Mots moyens: {stats['avg_words_original']} → {stats['avg_words_reconstructed']}")
            
            # Ajouter les stats à la métadata
            enriched_data["metadata"]["sentence_reconstruction"] = stats
            segments = reconstructed_segments
        else:
            segments = original_segments
        
        # Mettre à jour les segments dans les données enrichies
        enriched_data["transcription"]["segments"] = segments
        
        # Statistiques globales
        global_stats = defaultdict(list)
        total_segments_with_love = 0
        
        for i, segment in enumerate(segments):
            text = segment["text"]
            
            # Analyser le segment
            love_scores = self.analyze_segment(text)
            
            # Ajouter les scores au segment
            segment["love_analysis"] = love_scores
            
            # Déterminer le type d'amour dominant
            max_score = max(love_scores.values())
            if max_score > 0.1:  # Seuil minimum
                dominant_type = max(love_scores, key=love_scores.get)
                segment["dominant_love_type"] = dominant_type
                segment["love_confidence"] = float(max_score)  # Convertir en float Python
                total_segments_with_love += 1
            else:
                segment["dominant_love_type"] = "neutre"
                segment["love_confidence"] = 0.0
            
            # Collecter les statistiques
            for love_type, score in love_scores.items():
                global_stats[love_type].append(score)
        
        # Calculer les statistiques globales
        love_statistics = {}
        for love_type, scores in global_stats.items():
            if scores:  # Vérifier que la liste n'est pas vide
                love_statistics[love_type] = {
                    "average_score": float(round(np.mean(scores), 3)),
                    "max_score": float(round(np.max(scores), 3)),
                    "segments_count": int(sum(1 for s in scores if s > 0.1)),
                    "total_intensity": float(round(np.sum(scores), 3))
                }
            else:
                love_statistics[love_type] = {
                    "average_score": 0.0,
                    "max_score": 0.0,
                    "segments_count": 0,
                    "total_intensity": 0.0
                }
        
        # Ajouter les métadonnées d'analyse
        enriched_data["love_analysis"] = {
            "analyzer_version": "1.0",
            "analysis_date": transcription_data["metadata"]["transcription_date"],
            "categories_analyzed": list(self.love_categories.keys()),
            "total_segments": len(segments),
            "segments_with_love_content": total_segments_with_love,
            "love_coverage_percentage": round((total_segments_with_love / len(segments)) * 100, 1),
            "statistics_by_type": love_statistics
        }
        
        # Identifier les segments les plus représentatifs
        for love_type in self.love_categories.keys():
            representative_segments = []
            for segment in segments:
                score = segment["love_analysis"].get(love_type, 0)
                if score > 0.3:  # Seuil pour les segments représentatifs
                    representative_segments.append({
                        "segment_id": segment["id"],
                        "text": segment["text"],
                        "score": score,
                        "start": segment["start"],
                        "end": segment["end"]
                    })
            
            # Trier par score décroissant
            representative_segments.sort(key=lambda x: x["score"], reverse=True)
            love_statistics[love_type]["representative_segments"] = representative_segments[:3]  # Top 3
        
        print(f"✅ Analyse terminée : {total_segments_with_love}/{len(segments)} segments contiennent du contenu amoureux")
        
        # Nettoyer tous les types NumPy
        enriched_data = convert_numpy_types(enriched_data)
        
        return enriched_data
    
    def get_love_summary(self, enriched_data: Dict[str, Any]) -> str:
        """Génère un résumé textuel de l'analyse d'amour."""
        analysis = enriched_data["love_analysis"]
        stats = analysis["statistics_by_type"]
        
        summary = []
        summary.append("📊 ANALYSE DES TYPES D'AMOUR")
        summary.append("=" * 40)
        
        # Statistiques générales
        summary.append(f"💝 Couverture amour : {analysis['love_coverage_percentage']}% des segments")
        summary.append(f"🎬 Segments analysés : {analysis['total_segments']}")
        summary.append("")
        
        # Top types d'amour
        top_types = sorted(
            stats.items(), 
            key=lambda x: x[1]["total_intensity"], 
            reverse=True
        )[:3]
        
        summary.append("🏆 TOP 3 TYPES D'AMOUR :")
        for i, (love_type, data) in enumerate(top_types, 1):
            intensity = data["total_intensity"]
            avg_score = data["average_score"]
            segments = data["segments_count"]
            
            summary.append(f"   {i}. {love_type.upper()} :")
            summary.append(f"      • Intensité totale : {intensity}")
            summary.append(f"      • Score moyen : {avg_score}")
            summary.append(f"      • Segments concernés : {segments}")
            
            # Exemple représentatif
            if data["representative_segments"]:
                example = data["representative_segments"][0]
                summary.append(f"      • Exemple : \"{example['text'][:60]}...\"")
            summary.append("")
        
        return "\n".join(summary)