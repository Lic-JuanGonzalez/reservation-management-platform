import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  reservationsApi,
  type CreateReservationPayload,
} from "@/services/api/reservations";
import type { ReservationStatus } from "@/types";

export function useReservations(params: {
  status?: ReservationStatus;
  resource_id?: string;
  offset?: number;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: ["reservations", params],
    queryFn: () => reservationsApi.list(params),
    staleTime: 30_000,
  });
}

export function useReservation(id: string) {
  return useQuery({
    queryKey: ["reservations", id],
    queryFn: () => reservationsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateReservationPayload) =>
      reservationsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      toast.success("Reservation created successfully");
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to create reservation");
    },
  });
}

export function useCancelReservation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      reservationsApi.cancel(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      toast.success("Reservation cancelled");
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to cancel reservation");
    },
  });
}

export function useConfirmReservation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => reservationsApi.confirm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      toast.success("Reservation confirmed");
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || "Failed to confirm reservation");
    },
  });
}

export function useAvailability(resource_id: string, date: string) {
  return useQuery({
    queryKey: ["availability", resource_id, date],
    queryFn: () => reservationsApi.getAvailability(resource_id, date),
    enabled: !!resource_id && !!date,
    staleTime: 30_000,
  });
}
