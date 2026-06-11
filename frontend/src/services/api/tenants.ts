import { apiClient } from "./client";

export interface TenantSettings {
  timezone: string;
  locale: string;
  currency: string;
  date_format: string;
  time_format: string;
  max_advance_booking_days: number;
  min_advance_booking_hours: number;
  max_reservations_per_customer: number;
  cancellation_hours_before: number;
  slot_duration_minutes: number;
  require_email_verification: boolean;
  allow_guest_bookings: boolean;
  send_reminders: boolean;
  reminder_hours_before: number[];
}

export interface TenantDetail {
  id: string;
  name: string;
  slug: string;
  business_type: string;
  status: string;
  owner_email: string;
  logo_url: string | null;
  website: string | null;
  phone: string | null;
  address: string | null;
  settings: TenantSettings;
}

export const tenantsApi = {
  get: (id: string) =>
    apiClient.get<TenantDetail>(`/tenants/${id}`).then((r) => r.data),

  update: (id: string, payload: Partial<Pick<TenantDetail, "name" | "logo_url" | "website" | "phone" | "address">>) =>
    apiClient.patch<TenantDetail>(`/tenants/${id}`, payload).then((r) => r.data),

  updateSettings: (id: string, payload: Partial<TenantSettings>) =>
    apiClient.patch<TenantSettings>(`/tenants/${id}/settings`, payload).then((r) => r.data),
};
