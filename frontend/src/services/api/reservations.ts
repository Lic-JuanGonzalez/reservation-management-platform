import { apiClient } from "./client";
import type { AvailableSlot, PaginatedResponse, Reservation, ReservationStatus } from "@/types";

export interface CreateReservationPayload {
  resource_id: string;
  start_time: string;
  end_time: string;
  notes?: string;
}

export const reservationsApi = {
  list: (params: {
    status?: ReservationStatus;
    resource_id?: string;
    offset?: number;
    limit?: number;
  }) =>
    apiClient
      .get<PaginatedResponse<Reservation>>("/reservations", { params })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Reservation>(`/reservations/${id}`).then((r) => r.data),

  create: (payload: CreateReservationPayload) =>
    apiClient.post<Reservation>("/reservations", payload).then((r) => r.data),

  cancel: (id: string, reason?: string) =>
    apiClient
      .post<Reservation>(`/reservations/${id}/cancel`, { reason })
      .then((r) => r.data),

  confirm: (id: string) =>
    apiClient.post<Reservation>(`/reservations/${id}/confirm`).then((r) => r.data),

  getAvailability: (resource_id: string, date: string) =>
    apiClient
      .get<AvailableSlot[]>("/reservations/availability", {
        params: { resource_id, date },
      })
      .then((r) => r.data),
};
