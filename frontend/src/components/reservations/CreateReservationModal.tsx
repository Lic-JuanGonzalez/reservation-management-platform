import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { format } from "date-fns";
import { useResources } from "@/hooks/useResources";
import { useAvailability, useCreateReservation } from "@/hooks/useReservations";

interface Props {
  onClose: () => void;
}

export default function CreateReservationModal({ onClose }: Props) {
  const [resourceId, setResourceId] = useState("");
  const [date, setDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [selectedSlot, setSelectedSlot] = useState<{ start: string; end: string } | null>(null);
  const [notes, setNotes] = useState("");

  const { data: resources, isLoading: loadingResources } = useResources();
  const { data: slots, isLoading: loadingSlots } = useAvailability(resourceId, date);
  const createMutation = useCreateReservation();

  const handleSubmit = () => {
    if (!selectedSlot || !resourceId) return;
    createMutation.mutate(
      {
        resource_id: resourceId,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        notes: notes || undefined,
      },
      { onSuccess: onClose }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">New Reservation</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Resource */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Resource
            </label>
            {loadingResources ? (
              <div className="text-sm text-gray-400">Loading resources...</div>
            ) : (
              <select
                value={resourceId}
                onChange={(e) => { setResourceId(e.target.value); setSelectedSlot(null); }}
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select a resource...</option>
                {resources?.items.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.resource_type})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Date
            </label>
            <input
              type="date"
              value={date}
              min={format(new Date(), "yyyy-MM-dd")}
              onChange={(e) => { setDate(e.target.value); setSelectedSlot(null); }}
              className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Slots */}
          {resourceId && date && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Available Slots
              </label>
              {loadingSlots ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading slots...
                </div>
              ) : !slots?.length ? (
                <p className="text-sm text-gray-400">No slots available for this date.</p>
              ) : (
                <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                  {slots.map((slot) => {
                    const isSelected =
                      selectedSlot?.start === slot.start_time && selectedSlot?.end === slot.end_time;
                    return (
                      <button
                        key={slot.start_time}
                        type="button"
                        onClick={() => setSelectedSlot({ start: slot.start_time, end: slot.end_time })}
                        className={`py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                          isSelected
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-indigo-400"
                        }`}
                      >
                        {format(new Date(slot.start_time), "HH:mm")}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Notes <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Any special requests..."
              className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedSlot || !resourceId || createMutation.isPending}
            className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {createMutation.isPending ? "Creating..." : "Create Reservation"}
          </button>
        </div>
      </div>
    </div>
  );
}
