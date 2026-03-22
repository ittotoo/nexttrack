"""Spotify Web API client for fetching track data and audio features."""

from typing import List, Optional
import logging

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.models.track import Track, AudioFeatures
from app.config import settings

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Client for interacting with Spotify Web API. """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        
        self.client_id = client_id or settings.spotify_client_id
        self.client_secret = client_secret or settings.spotify_client_secret

        # Initialize Spotipy client
        auth_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Spotify client initialized successfully")

    def get_track(self, track_id: str) -> Optional[Track]:
        """Fetch track metadata from Spotify.  """
        try:
            track_data = self.sp.track(track_id)
            return self._parse_track(track_data)
        except Exception as e:
            logger.error(f"Error fetching track {track_id}: {e}")
            return None

    def get_tracks(self, track_ids: List[str]) -> List[Track]:
        
        if not track_ids:
            return []

        # Spotify API allows max 50 tracks per request
        tracks = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i : i + 50]
            try:
                results = self.sp.tracks(batch)
                for track_data in results["tracks"]:
                    if track_data:  # Some may be None if not found
                        tracks.append(self._parse_track(track_data))
            except Exception as e:
                logger.error(f"Error fetching tracks batch: {e}")

        return tracks

    def get_audio_features(self, track_id: str) -> Optional[AudioFeatures]:
        """Fetch audio features for a track. """
        try:
            features_data = self.sp.audio_features([track_id])[0]
            if not features_data:
                return None
            return self._parse_audio_features(features_data)
        except Exception as e:
            logger.error(f"Error fetching audio features for {track_id}: {e}")
            return None

    def get_audio_features_batch(self, track_ids: List[str]) -> List[Optional[AudioFeatures]]:
        """Fetch audio features for multiple tracks.  """
        if not track_ids:
            return []

        features = []
        
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i : i + 100]
            try:
                results = self.sp.audio_features(batch)
                for features_data in results:
                    if features_data:
                        features.append(self._parse_audio_features(features_data))
                    else:
                        features.append(None)
            except Exception as e:
                logger.error(f"Error fetching audio features batch: {e}")
                features.extend([None] * len(batch))

        return features

    def get_track_with_features(self, track_id: str) -> Optional[Track]:
        """Fetch track with audio features in one call.   """
        track = self.get_track(track_id)
        if not track:
            return None

        features = self.get_audio_features(track_id)
        track.features = features
        return track

    def get_tracks_with_features(self, track_ids: List[str]) -> List[Track]:
        """Fetch multiple tracks with audio features.  """
        tracks = self.get_tracks(track_ids)
        if not tracks:
            return []

        # Fetch audio features for all tracks
        track_id_list = [t.spotify_id for t in tracks]
        features_list = self.get_audio_features_batch(track_id_list)

        # Attach features to tracks
        for track, features in zip(tracks, features_list):
            track.features = features

        return tracks

    def search_tracks(self, query: str, limit: int = 20) -> List[Track]:
        """Search for tracks by name, artist, or other criteria.   """
        try:
            results = self.sp.search(q=query, type="track", limit=min(limit, 50))
            tracks = []
            for item in results["tracks"]["items"]:
                tracks.append(self._parse_track(item))
            return tracks
        except Exception as e:
            logger.error(f"Error searching tracks: {e}")
            return []

    def _parse_track(self, track_data: dict) -> Track:
        """Parse Spotify track API response into Track model. """
        return Track(
            spotify_id=track_data["id"],
            name=track_data["name"],
            artists=[artist["name"] for artist in track_data["artists"]],
            album=track_data["album"]["name"] if track_data.get("album") else None,
            release_date=track_data["album"].get("release_date") if track_data.get("album") else None,
            preview_url=track_data.get("preview_url"),
            popularity=track_data.get("popularity"),
        )

    def _parse_audio_features(self, features_data: dict) -> AudioFeatures:
        """Parse Spotify audio features API response into AudioFeatures model.  """
        return AudioFeatures(
            acousticness=features_data["acousticness"],
            danceability=features_data["danceability"],
            energy=features_data["energy"],
            instrumentalness=features_data["instrumentalness"],
            liveness=features_data["liveness"],
            loudness=features_data["loudness"],
            speechiness=features_data["speechiness"],
            valence=features_data["valence"],
            tempo=features_data["tempo"],
            time_signature=features_data["time_signature"],
            key=features_data["key"],
            mode=features_data["mode"],
            duration_ms=features_data["duration_ms"],
        )
