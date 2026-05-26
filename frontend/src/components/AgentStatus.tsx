"use client";

interface AgentStatusProps {
  statuses: string[];
}

export function AgentStatus({ statuses }: AgentStatusProps) {
  if (statuses.length === 0) return null;

  return (
    <div className="flex flex-col gap-1 mb-3">
      {statuses.map((status, i) => (
        <div
          key={i}
          className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 animate-fade-in"
        >
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          {status}
        </div>
      ))}
    </div>
  );
}
