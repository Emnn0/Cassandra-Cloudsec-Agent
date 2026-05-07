interface Column<T> {
  key: keyof T;
  header: string;
  render?: (val: T[keyof T], row: T) => React.ReactNode;
  align?: "left" | "right" | "center";
}

interface Props<T extends object> {
  title: string;
  rows: T[];
  columns: Column<T>[];
  emptyMessage?: string;
}

export function StatsTable<T extends object>({
  title,
  rows,
  columns,
  emptyMessage = "Veri yok.",
}: Props<T>) {
  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3.5 border-b border-[#1E3A5F] bg-[#132238]/50">
        <h3 className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest">{title}</h3>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-[#64748B] px-5 py-6 text-center font-mono">{emptyMessage}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#0D1B2E] text-xs font-semibold text-[#64748B] uppercase tracking-widest border-b border-[#1E3A5F]">
                {columns.map((col) => (
                  <th
                    key={String(col.key)}
                    className={`px-5 py-2.5 font-mono ${
                      col.align === "right"
                        ? "text-right"
                        : col.align === "center"
                        ? "text-center"
                        : "text-left"
                    }`}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E3A5F]">
              {rows.map((row, i) => (
                <tr key={i} className="hover:bg-[#132238]/60 transition-colors">
                  {columns.map((col) => (
                    <td
                      key={String(col.key)}
                      className={`px-5 py-3 text-[#E2E8F0] ${
                        col.align === "right"
                          ? "text-right tabular-nums font-mono"
                          : col.align === "center"
                          ? "text-center"
                          : ""
                      }`}
                    >
                      {col.render
                        ? col.render(row[col.key], row)
                        : String(row[col.key] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}