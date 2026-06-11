import { useState } from "react";
import { format } from "date-fns";
import { Calendar, Check, Plus, X } from "lucide-react";
import { useCancelReservation, useConfirmReservation, useReservations } from "@/hooks/useReservations";
import type { ReservationStatus } from "@/types";
import clsx from "clsx";
import CreateReservationModal from "@/components/reservations/CreateReservationModal";

const STATUS_CLASSES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  confirmed: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  completed: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
  no_show: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
  waitlisted: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
};

const STATUS_FILTERS: Array<{ label: string; value: ReservationStatus | "" }> = [
  { label: "All", value: "" },
  { label: "Pending", value: "pending" },
  { label: "Confirmed", value: "confirmed" },
  { label: "Completed", value: "completed" },
  { label: "Cancelled", value: "cancelled" },
];

export default function ReservationsPage() {
  const [statusFilter, setStatusFilter] = useState<ReservationStatus | "">("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data, isLoading } = useReservations({
    status: statusFilter || undefined,
    limit: 100,
  });

  const cancelMutation = useCancelReservation();
  const confirmMutation = useConfirmReservation();

  const handleCancel = (id: string) => {
    if (!window.confirm("Cancel this reservation?")) return;
    cancelMutation.mutate({ id });
  };

  const handleConfirm = (id: string) => {
    confirmMutation.mutate(id);
  };

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reservations</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Reservation
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setStatusFilter(value as ReservationStatus | "")}
            className={clsx(
              "px-3.5 py-1.5 text-sm font-medium rounded-lg transition-colors",
              statusFilter === value
                ? "bg-indigo-600 text-white"
                : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center text-gray-400">Loading...</div>
        ) : data?.items.length === 0 ? (
          <div className="py-20 text-center">
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No reservations found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                  {["Reference", "Status", "Start", "End", "Actions"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-gray-700">
                {data?.items.map((r) => (
                  <tr
                    key={r.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono font-medium text-gray-900 dark:text-white">
                      #{r.reference_number}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          "inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium capitalize",
                          STATUS_CLASSES[r.status]
                        )}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {format(new Date(r.start_time), "MMM d, yyyy HH:mm")}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {format(new Date(r.end_time), "HH:mm")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {r.status === "pending" && (
                          <button
                            onClick={() => handleConfirm(r.id)}
                            disabled={confirmMutation.isPending}
                            title="Confirm"
                            className="inline-flex items-center justify-center h-7 w-7 rounded-md bg-emerald-50 hover:bg-emerald-100 text-emerald-600 disabled:opacity-50 transition-colors"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                        )}
                        {["pending", "confirmed"].includes(r.status) && (
                          <button
                            onClick={() => handleCancel(r.id)}
                            disabled={cancelMutation.isPending}
                            title="Cancel"
                            className="inline-flex items-center justify-center h-7 w-7 rounded-md bg-red-50 hover:bg-red-100 text-red-600 disabled:opacity-50 transition-colors"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {data && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Showing {data.items.length} of {data.total} reservations
        </p>
      )}

      {showCreateModal && <CreateReservationModal onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}
