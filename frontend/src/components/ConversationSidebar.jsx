export default function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}) {
  return (
    <aside className="w-64 border-r border-border flex flex-col shrink-0">
      <div className="p-3 border-b border-border">
        <button
          onClick={onNew}
          className="w-full text-sm bg-verified text-ink font-medium py-2 rounded-md hover:opacity-90 transition-opacity"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 && (
          <p className="text-xs text-muted p-4 text-center">
            No conversations yet.
          </p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`group flex items-center justify-between gap-2 px-3 py-2.5 cursor-pointer border-l-2 transition-colors ${
              c.id === activeId
                ? "border-verified bg-panelLight"
                : "border-transparent hover:bg-panelLight"
            }`}
          >
            <span className="text-sm text-text truncate">{c.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              className="opacity-0 group-hover:opacity-100 text-muted hover:text-danger text-xs transition-opacity shrink-0"
              aria-label="Delete conversation"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}