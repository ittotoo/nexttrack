import { useState, useRef, useEffect } from "react";
import type { Track } from "../types/api";
import { useSearch } from "../hooks/useSearch";
import TrackCard from "./TrackCard";

interface SearchBarProps {
  onSelect: (track: Track) => void;
  disabled?: boolean;
}

export default function SearchBar({ onSelect, disabled }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const { results, loading } = useSearch(query);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Open dropdown when results arrive
  useEffect(() => {
    if (results.length > 0 && query.length > 0) setOpen(true);
  }, [results, query]);

  function select(track: Track) {
    onSelect(track);
    setQuery("");
    setOpen(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open || results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault();
      select(results[activeIndex]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    }
  }

  return (
    <div ref={containerRef} className="relative" role="search">
      <label htmlFor="track-search" className="sr-only">
        Search for tracks
      </label>
      <div className="relative">
        <input
          ref={inputRef}
          id="track-search"
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setActiveIndex(-1);
          }}
          onFocus={() => results.length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search for a song or artist..."
          disabled={disabled}
          className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm placeholder-gray-400 shadow-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
          role="combobox"
          aria-expanded={open}
          aria-controls="search-results"
          aria-activedescendant={
            activeIndex >= 0 ? `search-result-${activeIndex}` : undefined
          }
          autoComplete="off"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          </div>
        )}
      </div>

      {open && results.length > 0 && (
        <ul
          id="search-results"
          role="listbox"
          className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg"
        >
          {results.map((track, i) => (
            <li
              key={track.spotify_id}
              id={`search-result-${i}`}
              role="option"
              aria-selected={i === activeIndex}
              className={`cursor-pointer border-b border-gray-100 last:border-0 hover:bg-gray-50 ${
                i === activeIndex ? "bg-brand-50" : ""
              }`}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseDown={(e) => {
                e.preventDefault(); // prevent blur before click fires
                select(track);
              }}
            >
              <TrackCard track={track} compact />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
