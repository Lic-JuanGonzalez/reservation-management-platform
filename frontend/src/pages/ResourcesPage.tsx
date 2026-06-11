import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Package, Plus, Edit2, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { resourcesApi } from "@/services/api/resources";
import type { Resource, ResourceStatus } from "@/types";
import clsx from "clsx";
import ResourceModal from "@/components/resources/ResourceModal";

const STATUS_CLASSES: Record<ResourceStatus, string> = {
  active: "bg-emerald-100 text-emerald-700",
  inactive: "bg-gray-100 text-gray-600",
  maintenance: "bg-amber-100 text-amber-700",
};

const TYPE_LABELS: Record<string, string> = {
  room: "Room",
  staff: "Staff",
  equipment: "Equipment",
  space: "Space",
  service: "Service",
};

export default function ResourcesPage() {
  const queryClient = useQueryClient();
  const [modalResource, setModalResource] = useState<Resource | null | undefined>(undefined);

  const { data, isLoading } = useQuery({
    queryKey: ["resources"],
    queryFn: () => resourcesApi.list({ limit: 100 }),
    staleTime: 60_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => resourcesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] });
      toast.success("Resource deleted");
    },
    onError: () => toast.error("Failed to delete resource"),
  });

  const handleDelete = (id: string) => {
    if (!window.confirm("Delete this resource? Existing reservations will be unaffected.")) return;
    deleteMutation.mutate(id);
  };

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Resources</h1>
        <button
          onClick={() => setModalResource(null)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Resource
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-gray-400">Loading...</div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-20">
          <Package className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No resources yet. Create your first resource.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((resource) => (
            <div
              key={resource.id}
              className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{resource.name}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {TYPE_LABELS[resource.resource_type]}
                  </p>
                </div>
                <span
                  className={clsx(
                    "text-xs px-2 py-0.5 rounded-full font-medium capitalize",
                    STATUS_CLASSES[resource.status]
                  )}
                >
                  {resource.status}
                </span>
              </div>

              <div className="space-y-1.5 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex justify-between">
                  <span>Capacity</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {resource.capacity}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Slot duration</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {resource.slot_duration_minutes} min
                  </span>
                </div>
                {resource.amenities.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-2">
                    {resource.amenities.slice(0, 3).map((a) => (
                      <span
                        key={a}
                        className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400"
                      >
                        {a}
                      </span>
                    ))}
                    {resource.amenities.length > 3 && (
                      <span className="text-xs text-gray-400">
                        +{resource.amenities.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                <button
                  onClick={() => setModalResource(resource)}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 transition-colors"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(resource.id)}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-red-600 transition-colors ml-auto"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {modalResource !== undefined && (
        <ResourceModal
          resource={modalResource ?? undefined}
          onClose={() => setModalResource(undefined)}
        />
      )}
    </div>
  );
}
