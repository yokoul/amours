#!/usr/bin/env python3
"""
Compare l'ancienne liste de mots avec la nouvelle extraite des audios.
"""

# Ancienne liste (120 mots)
old_words = [
    'passion', 'désir', 'tendresse', 'émotion', 'flamme',
    'cœur', 'âme', 'rêve', 'espoir', 'joie',
    'bonheur', 'extase', 'ivresse', 'folie', 'délire',
    'baiser', 'caresse', 'étreinte', 'regard', 'sourire',
    'larme', 'soupir', 'frisson', 'trouble', 'émoi',
    'séduction', 'charme', 'beauté', 'grâce', 'élégance',
    'étoile', 'lune', 'soleil', 'nuit', 'jour',
    'silence', 'murmure', 'chanson', 'mélodie', 'harmonie',
    'danse', 'valse', 'élan', 'envol', 'fuite',
    'lumière', 'vertige', 'abandon', 'mystère', 'délice',
    'fusion', 'souffle', 'éternité', 'instant', 'promesse',
    'amant', 'attente', 'nostalgie', 'souvenir', 'rencontre',
    'adieu', 'absence', 'présence', 'douceur', 'chaleur',
    'feu', 'ardeur', 'langueur', 'tourment', 'supplice',
    'ravissement', 'enchantement', 'émerveillement', 'plaisir', 'volupté',
    'confidence', 'secret', 'aveu', 'serment', 'fidélité',
    'trahison', 'jalousie', 'tristesse', 'mélancolie', 'chagrin',
    'consolation', 'réconfort', 'apaisement', 'sérénité', 'paix',
    'tempête', 'orage', 'calme', 'brise', 'vent',
    'mer', 'vague', 'rivage', 'horizon', 'infini',
    'rire', 'pleur', 'sanglot', 'gémissement', 'cri',
    'voix', 'parole', 'mot', 'lettre', 'message',
    'toucher', 'peau', 'corps', 'main', 'lèvre',
    'œil', 'visage', 'cheveux', 'parfum', 'odeur',
    'goût', 'saveur', 'sensation', 'sentiment', 'impression'
]

# Nouvelle liste (112 mots extraits des audios)
new_words = [
    'amour', 'dire', 'moment', 'temps', 'petit', 'envie',
    'toujours', 'voir', 'parler', 'peur', 'aimer', 'émotion',
    'plein', 'famille', 'besoin', 'mère', 'amoureux', 'père',
    'amitié', 'jamais', 'fort', 'amoureuse', 'corps', 'grand',
    'vient', 'sentiment', 'couple', 'enfant', 'passé', 'mots',
    'regarder', 'aimerais', 'maison', 'manque', 'joie', 'partir',
    'colère', 'entendre', 'présent', 'cœur', 'rester', 'écouter',
    'amours', 'tristesse', 'rencontre', 'ville', 'désir', 'yeux',
    'instant', 'visage', 'venir', 'voix', 'mort', 'sentir',
    'frère', 'viens', 'amoureuses', 'passion', 'devient', 'tomber',
    'revient', 'mariage', 'souvenir', 'odeur', 'reviens', 'viennent',
    'lumière', 'esprit', 'toucher', 'lieu', 'absence', 'terre',
    'sang', 'main', 'sourire', 'souviens', 'haine', 'vide',
    'bonheur', 'pensée', 'jalousie', 'attente', 'regard', 'léger',
    'amant', 'trahison', 'sœur', 'jardin', 'séparation', 'présence',
    'distance', 'divorce', 'chaud', 'mémoire', 'envies', 'espoir',
    'profond', 'polyamour', 'marcher', 'vies', 'tendresse', 'couleur',
    'chambre', 'deviens', 'fidélité', 'futur', 'vienne', 'chant',
    'cheveux', 'hier', 'nostalgie', 'froid'
]

old_set = set(old_words)
new_set = set(new_words)

print("=" * 70)
print("COMPARAISON DES VOCABULAIRES")
print("=" * 70)

print(f"\n📊 STATISTIQUES:")
print(f"  Ancienne liste : {len(old_words)} mots")
print(f"  Nouvelle liste : {len(new_words)} mots")
print(f"  En commun     : {len(old_set & new_set)} mots")

print(f"\n✅ MOTS CONSERVÉS ({len(old_set & new_set)}) :")
print("-" * 70)
common = sorted(old_set & new_set)
for i in range(0, len(common), 6):
    print("  " + ", ".join(common[i:i+6]))

print(f"\n❌ MOTS PERDUS ({len(old_set - new_set)}) - Pas dans les audios :")
print("-" * 70)
lost = sorted(old_set - new_set)
for i in range(0, len(lost), 6):
    print("  " + ", ".join(lost[i:i+6]))

print(f"\n🆕 NOUVEAUX MOTS ({len(new_set - old_set)}) - Trouvés dans les audios :")
print("-" * 70)
gained = sorted(new_set - old_set)
for i in range(0, len(gained), 6):
    print("  " + ", ".join(gained[i:i+6]))

print("\n" + "=" * 70)
print("RECOMMANDATION:")
print("=" * 70)
print("""
La nouvelle liste contient des mots réellement prononcés dans vos interviews.
Cela garantit que les phrases générées pourront être assemblées avec les audios.

Mots poétiques perdus mais pas dans les audios:
- Très littéraires: extase, ivresse, délire, ravissement, enchantement
- Abstraits: âme, rêve, mystère, infini, éternité
- Physiques: baiser, caresse, étreinte, lèvre, peau
- Naturels: étoile, lune, mer, vague, orage

Nouveaux mots ajoutés (du corpus réel):
- Relationnels: famille, mère, père, frère, sœur, enfant
- Temporels: moment, temps, passé, présent, futur, hier
- Actions: dire, parler, voir, aimer, partir, rester
- Émotions réelles: peur, colère, haine, manque
- Concepts modernes: polyamour, divorce

💡 CONSEIL: Vous pourriez faire un mix:
   - Garder les mots du corpus (garantis disponibles)
   - Ajouter manuellement quelques mots poétiques clés si vous avez ces sons
""")
