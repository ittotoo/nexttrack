export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold text-brand-700">NextTrack</h1>
        <p className="mt-1 text-gray-600">
          Privacy-preserving music recommendations — no tracking, no accounts,
          no stored data.
        </p>
      </div>
    </header>
  );
}
