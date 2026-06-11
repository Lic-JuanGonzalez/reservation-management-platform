import { useEffect, useState } from "react";
import { X, Loader2, Plus, Minus } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { resourcesApi, type CreateResourcePayload } from "@/services/api/resources";
import type { Resource, ResourceType } from "@/types";

const RESOURCE_TYPES: ResourceType[] = ["room", "staff", "equipment", "space", "service"];

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

interface Props {
  resource?: Resource;
  onClose: () => void;
}

type DayHours = { start: string; end: string } | null;

const DEFAULT_HOURS: Record<string, DayHours> = {
  monday: { start: "09:00", end: "18:00" },
  tuesday: { start: "09:00", end: "18:00" },
  wednesday: { start: "09:00", end: "18:00" },
  thursday: { start: "09:00", end: "18:00" },
  friday: { start: "09:00", end: "18:00" },
  saturday: null,
  sunday: null,
};

export default function ResourceModal({ resource, onClose }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!resource;

  const [name, setName] = useState(resource?.name ?? "");
  const [type, setType] = useState<ResourceType>(resource?.resource_type ?? "room");
  const [description, setDescription] = useState(resource?.description ?? "");
  const [capacity, setCapacity] = useState(resource?.capacity ?? 1);
  const [slotDuration, setSlotDuration] = useState(resource?.slot_duration_minutes ?? 60);
  const [buffer, setBuffer] = useState(resource?.buffer_minutes ?? 0);
  const [amenityInput, setAmenityInput] = useState("");
  const [amenities, setAmenities] = useState<string[]>(resource?.amenities ?? []);
  const [hours, setHours] = useState<Record<string, DayHours>>(DEFAULT_HOURS);

  const mutation = useMutation({
    mutationFn: (payload: CreateResourcePayload) =>
      isEdit ? resourcesApi.update(resource.id, payload) : resourcesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] });
      toast.success(isEdit ? "Resource updated" : "Resource created");
      onClose();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to save resource");
    },
  });

  const handleSubmit = () => {
    if (!name.trim()) return toast.error("Name is required");
    const working_hours: Record<string, Array<{ start: string; end: string }>> = {};
    DAYS.forEach((day) => {
      working_hours[day] = hours[day] ? [hours[day]!] : [];
    });
    mutation.mutate({
      name: name.trim(),
      resource_type: type,
      description: description.trim() || undefined,
      capacity,
      slot_duration_minutes: slotDuration,
      buffer_minutes: buffer,
      amenities,
      working_hours,
    });
  };

  const addAmenity = () => {
    const val = amenityInput.trim();
    if (val && !amenities.includes(val)) setAmenities([...amenities, val]);
    setAmenityInput("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {isEdit ? "Edit Resource" : "Add Resource"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {/* Name + Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Meeting Room A"
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as ResourceType)}
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {RESOURCE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          {/* Capacity + Slot + Buffer */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Capacity
              </label>
              <input
                type="number" min={1} value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Slot (min)
              </label>
              <input
                type="number" min={15} step={15} value={slotDuration}
                onChange={(e) => setSlotDuration(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Buffer (min)
              </label>
              <input
                type="number" min={0} step={5} value={buffer}
                onChange={(e) => setBuffer(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Amenities
            </label>
            <div className="flex gap-2">
              <input
                value={amenityInput}
                onChange={(e) => setAmenityInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addAmenity())}
                placeholder="e.g. WiFi"
                className="flex-1 px-3.5 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                type="button"
                onClick={addAmenity}
                className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            {amenities.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {amenities.map((a) => (
                  <span
                    key={a}
                    className="flex items-center gap-1 text-xs px-2 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full"
                  >
                    {a}
                    <button onClick={() => setAmenities(amenities.filter((x) => x !== a))}>
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Working Hours */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Working Hours
            </label>
            <div className="space-y-2">
              {DAYS.map((day) => (
                <div key={day} className="flex items-center gap-3">
                  <div className="w-24 flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!hours[day]}
                      onChange={(e) =>
                        setHours((h) => ({
                          ...h,
                          [day]: e.target.checked ? { start: "09:00", end: "18:00" } : null,
                        }))
                      }
                      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{day.slice(0, 3)}</span>
                  </div>
                  {hours[day] ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="time"
                        value={hours[day]!.start}
                        onChange={(e) =>
                          setHours((h) => ({ ...h, [day]: { ...h[day]!, start: e.target.value } }))
                        }
                        className="px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                      <span className="text-gray-400 text-sm">–</span>
                      <input
                        type="time"
                        value={hours[day]!.end}
                        onChange={(e) =>
                          setHours((h) => ({ ...h, [day]: { ...h[day]!, end: e.target.value } }))
                        }
                        className="px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">Closed</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex-shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={mutation.isPending}
            className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {mutation.isPending ? "Saving..." : isEdit ? "Save Changes" : "Create Resource"}
          </button>
        </div>
      </div>
    </div>
  );
}
