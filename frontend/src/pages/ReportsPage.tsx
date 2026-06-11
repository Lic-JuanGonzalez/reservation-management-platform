import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subDays, startOfMonth, endOfMonth } from "date-fns";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { TrendingUp, Calendar, CheckCircle, XCircle } from "lucide-react";
import { reportsApi } from "@/services/api/reports";

const STATUS_COLORS: Record<string, string> = {
  confirmed: "#10B981",
  completed: "#6366F1",
  pending: "#F59E0B",
  cancelled: "#EF4444",
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl shadow-lg p-3 min-w-[140px]">
      <p className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 text-xs py-0.5">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full inline-block" style={{ backgroundColor: entry.fill }} />
            <span className="text-gray-500 dark:text-gray-400 capitalize">{entry.dataKey}</span>
          </div>
          <span className="font-semibold text-gray-800 dark:text-gray-100">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

const PRESETS = [
  { label: "Last 7 days", start: () => format(subDays(new Date(), 6), "yyyy-MM-dd"), end: () => TODAY },
  { label: "Last 30 days", start: () => format(subDays(new Date(), 29), "yyyy-MM-dd"), end: () => TODAY },
  { label: "This month", start: () => format(startOfMonth(new Date()), "yyyy-MM-dd"), end: () => format(endOfMonth(new Date()), "yyyy-MM-dd") },
];

const TODAY = format(new Date(), "yyyy-MM-dd");

export default function ReportsPage() {
  const [startDate, setStartDate] = useState(format(startOfMonth(new Date()), "yyyy-MM-dd"));
  const [endDate, setEndDate] = useState(format(endOfMonth(new Date()), "yyyy-MM-dd"));

  const daysDiff = Math.abs((new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000);

  const { data: daily, isLoading: loadingDaily, isError: dailyError } = useQuery({
    queryKey: ["reports", "daily", startDate, endDate],
    queryFn: () => reportsApi.daily(startDate, endDate),
    staleTime: 60_000,
    enabled: daysDiff <= 365,
  });

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["reports", "summary", startDate, endDate],
    queryFn: () => reportsApi.summary(startDate, endDate),
    staleTime: 60_000,
  });

  const chartData = (daily ?? []).map((d) => ({
    ...d,
    date: format(new Date(d.date + "T12:00:00"), "MMM d"),
  }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>

        {/* Date controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => { setStartDate(p.start()); setEndDate(p.end()); }}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              {p.label}
            </button>
          ))}
          <div className="flex items-center gap-2">
            <input
              type="date" value={startDate} max={endDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-2.5 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <span className="text-gray-400 text-xs">–</span>
            <input
              type="date" value={endDate} min={startDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-2.5 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-xs bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total", value: summary?.total_reservations ?? 0, icon: Calendar, color: "bg-indigo-500" },
          { label: "Confirmed", value: summary?.confirmed ?? 0, icon: CheckCircle, color: "bg-emerald-500" },
          { label: "Completed", value: summary?.completed ?? 0, icon: TrendingUp, color: "bg-blue-500" },
          { label: "Cancelled", value: summary?.cancelled ?? 0, icon: XCircle, color: "bg-red-500" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className={`inline-flex p-2 rounded-lg ${color} mb-3`}>
              <Icon className="h-4 w-4 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{loadingSummary ? "—" : value}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Cancellation rate */}
      {summary && summary.total_reservations > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Cancellation rate</span>
            <span className="text-sm font-bold text-red-500">{summary.cancellation_rate.toFixed(1)}%</span>
          </div>
          <div className="mt-2 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-red-400 rounded-full"
              style={{ width: `${Math.min(summary.cancellation_rate, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Daily chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Daily Breakdown</h2>
        {daysDiff > 365 ? (
          <div className="h-48 flex items-center justify-center text-amber-500 text-sm">Date range exceeds 365 days</div>
        ) : loadingDaily ? (
          <div className="h-48 flex items-center justify-center text-gray-400">Loading...</div>
        ) : chartData.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data for this period</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData} barSize={14} barCategoryGap="30%">
              <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99,102,241,0.05)" }} />
              <Legend
                wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
                formatter={(value) => <span style={{ color: "#6B7280", textTransform: "capitalize" }}>{value}</span>}
              />
              <Bar dataKey="confirmed" fill={STATUS_COLORS.confirmed} name="confirmed" radius={[4, 4, 0, 0]} />
              <Bar dataKey="completed" fill={STATUS_COLORS.completed} name="completed" radius={[4, 4, 0, 0]} />
              <Bar dataKey="pending" fill={STATUS_COLORS.pending} name="pending" radius={[4, 4, 0, 0]} />
              <Bar dataKey="cancelled" fill={STATUS_COLORS.cancelled} name="cancelled" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
