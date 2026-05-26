"use client";

interface ProviderSelectorProps {
  providers: string[];
  current: string;
  onChange: (provider: string) => void;
}

export function ProviderSelector({
  providers,
  current,
  onChange,
}: ProviderSelectorProps) {
  return (
    <select
      value={current}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-300
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      {providers.map((p) => (
        <option key={p} value={p}>
          {p.charAt(0).toUpperCase() + p.slice(1)}
        </option>
      ))}
    </select>
  );
}
