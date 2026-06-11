import { apiClient } from "./client";
import type { PaginatedResponse, Resource, ResourceStatus, ResourceType } from "@/types";

export interface CreateResourcePayload {
  name: string;
  resource_type: ResourceType;
  description?: string;
  capacity?: number;
  slot_duration_minutes?: number;
  buffer_minutes?: number;
  amenities?: string[];
  working_hours?: Record<string, Array<{ start: string; end: string }>>;
}

export const resourcesApi = {
  list: (params: {
    resource_type?: ResourceType;
    status?: ResourceStatus;
    offset?: number;
    limit?: number;
  }) =>
    apiClient
      .get<PaginatedResponse<Resource>>("/resources", { params })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Resource>(`/resources/${id}`).then((r) => r.data),

  create: (payload: CreateResourcePayload) =>
    apiClient.post<Resource>("/resources", payload).then((r) => r.data),

  update: (id: string, payload: Partial<CreateResourcePayload> & { status?: ResourceStatus }) =>
    apiClient.patch<Resource>(`/resources/${id}`, payload).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/resources/${id}`),
};
