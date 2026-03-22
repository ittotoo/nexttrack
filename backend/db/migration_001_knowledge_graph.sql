-- NextTrack Knowledge Graph Migration



CREATE TABLE IF NOT EXISTS artist_relationships (
    artist_id_1 INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    artist_id_2 INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    weight FLOAT NOT NULL CHECK (weight >= 0 AND weight <= 1.0),
    evidence_count INTEGER DEFAULT 1,
    PRIMARY KEY (artist_id_1, artist_id_2, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_artist_rel_1 ON artist_relationships(artist_id_1);
CREATE INDEX IF NOT EXISTS idx_artist_rel_2 ON artist_relationships(artist_id_2);
CREATE INDEX IF NOT EXISTS idx_artist_rel_type ON artist_relationships(relationship_type);

COMMENT ON TABLE artist_relationships IS 'Artist knowledge graph edges derived from track co-occurrence and genre proximity';
COMMENT ON COLUMN artist_relationships.relationship_type IS 'collaboration (1.0), shared_album (0.7), or shared_genre (varies)';
COMMENT ON COLUMN artist_relationships.weight IS 'Relationship strength: collaboration=1.0, shared_album=0.7, genre-dependent';
COMMENT ON COLUMN artist_relationships.evidence_count IS 'Number of shared tracks/albums supporting this relationship';


CREATE TABLE IF NOT EXISTS genre_similarity (
    genre_1 VARCHAR(100) NOT NULL,
    genre_2 VARCHAR(100) NOT NULL,
    similarity FLOAT NOT NULL CHECK (similarity >= 0 AND similarity <= 1.0),
    PRIMARY KEY (genre_1, genre_2)
);

CREATE INDEX IF NOT EXISTS idx_genre_sim_1 ON genre_similarity(genre_1);
CREATE INDEX IF NOT EXISTS idx_genre_sim_2 ON genre_similarity(genre_2);

COMMENT ON TABLE genre_similarity IS 'Precomputed genre similarity based on taxonomic hierarchy (15 supergenres)';
