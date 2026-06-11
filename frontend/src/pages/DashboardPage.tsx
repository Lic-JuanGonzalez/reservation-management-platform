import { useQuery } from "@tanstack/react-query";
import { Calendar, Clock, CheckCircle, XCircle, TrendingUp } from "lucide-react";
import { format, startOfToday } from "date-fns";
import { useReservations } from "@/hooks/useReservations";
import { useAuthStore } from "@/store/authStore";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const entry = payload[0];
  return (
    <div
      className="rounded-lg shadow-lg overflow-hidden text-xs font-medium"
      style={{ border: `1.5px solid ${entry.fill}20`, background: "white" }}
    >
      <div className="h-1 w-full" style={{ backgroundColor: entry.fill }} />
      <div className="px-3 py-2 flex items-center gap-3">
        <span className="text-gray-500 capitalize">{label}</span>
        <span className="font-bold text-gray-900" style={{ color: entry.fill }}>{entry.value}</span>
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  pending: "#F59E0B",
  confirmed: "#10B981",
  cancelled: "#EF4444",
  completed: "#6366F1",
};

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
      <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const today = startOfToday();

  const { data: allReservations } = useReservations({ limit: 200 });
  const { data: todayReservations } = useReservations({
    limit: 50,
  });

  const total = allReservations?.total ?? 0;
  const confirmed = allReservations?.items.filter((r) => r.status === "confirmed").length ?? 0;
  const pending = allReservations?.items.filter((r) => r.status === "pending").length ?? 0;
  const cancelled = allReservations?.items.filter((r) => r.status === "cancelled").length ?? 0;
  const completed = allReservations?.items.filter((r) => r.status === "completed").length ?? 0;

  const recentReservations = allReservations?.items.slice(0, 5) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Good {getGreeting()}, {user?.first_name}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
          {format(new Date(), "EEEE, MMMM d, yyyy")}
        </p>
      </div>

      {/* Stats */}
      <div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-2 font-medium uppercase tracking-wide">All time</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total" value={total} icon={Calendar} color="bg-indigo-500" />
          <StatCard label="Confirmed" value={confirmed} icon={CheckCircle} color="bg-emerald-500" />
          <StatCard label="Pending" value={pending} icon={Clock} color="bg-amber-500" />
          <StatCard label="Cancelled" value={cancelled} icon={XCircle} color="bg-red-500" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" />
            Reservation Status Overview
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={[
                { name: "Pending", value: pending },
                { name: "Confirmed", value: confirmed },
                { name: "Completed", value: completed },
                { name: "Cancelled", value: cancelled },
              ]}
            >
              <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99,102,241,0.05)" }} offset={0} position={{ y: 20 }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {["pending", "confirmed", "completed", "cancelled"].map((status) => (
                  <Cell key={status} fill={STATUS_COLORS[status]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent reservations */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">
            Recent Reservations
          </h2>
          {recentReservations.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No reservations yet</p>
          ) : (
            <div className="space-y-3">
              {recentReservations.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700"
                >
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      #{r.reference_number}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {format(new Date(r.start_time), "MMM d, HH:mm")}
                    </div>
                  </div>
                  <span
                    className="text-xs px-2.5 py-1 rounded-full font-medium capitalize"
                    style={{
                      backgroundColor: `${STATUS_COLORS[r.status]}20`,
                      color: STATUS_COLORS[r.status],
                    }}
                  >
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}
