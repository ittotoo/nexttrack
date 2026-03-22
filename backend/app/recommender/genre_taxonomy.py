"""Genre taxonomy for knowledge graph genre proximity scoring."""

from typing import Dict, Optional

# Mapping of every genre in the database to its supergenre
GENRE_TO_SUPERGENRE: Dict[str, str] = {
    # ROCK
    "rock": "ROCK",
    "alt-rock": "ROCK",
    "hard-rock": "ROCK",
    "psych-rock": "ROCK",
    "rock-n-roll": "ROCK",
    "rockabilly": "ROCK",
    "grunge": "ROCK",
    "emo": "ROCK",
    "goth": "ROCK",
    "indie": "ROCK",
    "alternative": "ROCK",
    "british": "ROCK",
    # METAL
    "metal": "METAL",
    "heavy-metal": "METAL",
    "black-metal": "METAL",
    "death-metal": "METAL",
    "metalcore": "METAL",
    "grindcore": "METAL",
    "hardcore": "METAL",
    "industrial": "METAL",
    # PUNK
    "punk": "PUNK",
    "punk-rock": "PUNK",
    "ska": "PUNK",
    # ELECTRONIC
    "electronic": "ELECTRONIC",
    "edm": "ELECTRONIC",
    "house": "ELECTRONIC",
    "deep-house": "ELECTRONIC",
    "progressive-house": "ELECTRONIC",
    "chicago-house": "ELECTRONIC",
    "techno": "ELECTRONIC",
    "detroit-techno": "ELECTRONIC",
    "minimal-techno": "ELECTRONIC",
    "trance": "ELECTRONIC",
    "dubstep": "ELECTRONIC",
    "drum-and-bass": "ELECTRONIC",
    "breakbeat": "ELECTRONIC",
    "electro": "ELECTRONIC",
    "idm": "ELECTRONIC",
    "hardstyle": "ELECTRONIC",
    "synth-pop": "ELECTRONIC",
    "garage": "ELECTRONIC",
    # POP
    "pop": "POP",
    "indie-pop": "POP",
    "power-pop": "POP",
    "k-pop": "POP",
    "j-pop": "POP",
    "cantopop": "POP",
    "mandopop": "POP",
    "pop-film": "POP",
    # HIP_HOP
    "hip-hop": "HIP_HOP",
    "r-n-b": "HIP_HOP",
    "trip-hop": "HIP_HOP",
    # JAZZ_BLUES
    "jazz": "JAZZ_BLUES",
    "blues": "JAZZ_BLUES",
    # CLASSICAL
    "classical": "CLASSICAL",
    "opera": "CLASSICAL",
    "piano": "CLASSICAL",
    # FOLK_COUNTRY
    "folk": "FOLK_COUNTRY",
    "singer-songwriter": "FOLK_COUNTRY",
    "acoustic": "FOLK_COUNTRY",
    "bluegrass": "FOLK_COUNTRY",
    "country": "FOLK_COUNTRY",
    "honky-tonk": "FOLK_COUNTRY",
    "guitar": "FOLK_COUNTRY",
    # LATIN
    "latin": "LATIN",
    "latino": "LATIN",
    "salsa": "LATIN",
    "samba": "LATIN",
    "reggaeton": "LATIN",
    "forro": "LATIN",
    "pagode": "LATIN",
    "sertanejo": "LATIN",
    "tango": "LATIN",
    "brazil": "LATIN",
    "mpb": "LATIN",
    "spanish": "LATIN",
    # SOUL_FUNK
    "soul": "SOUL_FUNK",
    "funk": "SOUL_FUNK",
    "disco": "SOUL_FUNK",
    "groove": "SOUL_FUNK",
    "gospel": "SOUL_FUNK",
    # REGGAE
    "reggae": "REGGAE",
    "dancehall": "REGGAE",
    "dub": "REGGAE",
    # WORLD
    "world-music": "WORLD",
    "indian": "WORLD",
    "iranian": "WORLD",
    "turkish": "WORLD",
    "malay": "WORLD",
    "afrobeat": "WORLD",
    "french": "WORLD",
    "german": "WORLD",
    "swedish": "WORLD",
    # AMBIENT
    "ambient": "AMBIENT",
    "chill": "AMBIENT",
    "sleep": "AMBIENT",
    "new-age": "AMBIENT",
    "study": "AMBIENT",
    # CHILDREN
    "children": "CHILDREN",
    "kids": "CHILDREN",
    "disney": "CHILDREN",
    "anime": "CHILDREN",
    # MOOD_ACTIVITY (genres defined by mood/activity rather than musical style)
    "happy": "MOOD_ACTIVITY",
    "sad": "MOOD_ACTIVITY",
    "party": "MOOD_ACTIVITY",
    "club": "MOOD_ACTIVITY",
    "dance": "MOOD_ACTIVITY",
    "comedy": "MOOD_ACTIVITY",
    "show-tunes": "MOOD_ACTIVITY",
    "romance": "MOOD_ACTIVITY",
    # JAPANESE (distinct cultural grouping)
    "j-rock": "JAPANESE",
    "j-dance": "JAPANESE",
    "j-idol": "JAPANESE",
}

RELATED_SUPERGENRES = {
    frozenset({"ROCK", "METAL"}),
    frozenset({"ROCK", "PUNK"}),
    frozenset({"METAL", "PUNK"}),
    frozenset({"ELECTRONIC", "AMBIENT"}),
    frozenset({"POP", "ELECTRONIC"}),
    frozenset({"HIP_HOP", "SOUL_FUNK"}),
    frozenset({"JAZZ_BLUES", "SOUL_FUNK"}),
    frozenset({"FOLK_COUNTRY", "JAZZ_BLUES"}),
    frozenset({"REGGAE", "SOUL_FUNK"}),
    frozenset({"LATIN", "WORLD"}),
    frozenset({"POP", "MOOD_ACTIVITY"}),
    frozenset({"JAPANESE", "POP"}),
}


def get_supergenre(genre: str) -> Optional[str]:
    """Return the parent group for a genre, if known.    """
    return GENRE_TO_SUPERGENRE.get(genre)


def get_genre_similarity(genre_1: str, genre_2: str) -> float:
    """Return a simple taxonomy-based similarity score.  """
    if genre_1 == genre_2:
        return 1.0

    sg1 = GENRE_TO_SUPERGENRE.get(genre_1)
    sg2 = GENRE_TO_SUPERGENRE.get(genre_2)

    if sg1 is None or sg2 is None:
        return 0.0

    if sg1 == sg2:
        return 0.5

    if frozenset({sg1, sg2}) in RELATED_SUPERGENRES:
        return 0.25

    return 0.0
