export type UserRole = "super_admin" | "tenant_admin" | "employee" | "customer";
export type UserStatus = "active" | "inactive" | "pending_verification" | "suspended";
export type ReservationStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show"
  | "waitlisted";
export type ResourceType = "room" | "staff" | "equipment" | "space" | "service";
export type ResourceStatus = "active" | "inactive" | "maintenance";
export type BusinessType =
  | "hotel"
  | "medical_clinic"
  | "dental_office"
  | "gym"
  | "beauty_salon"
  | "coworking"
  | "event_venue"
  | "professional_services"
  | "other";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  status: UserStatus;
  tenant_id: string | null;
  phone: string | null;
  avatar_url: string | null;
  email_verified: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  business_type: BusinessType;
  status: string;
  owner_email: string;
  logo_url: string | null;
  website: string | null;
  phone: string | null;
  address: string | null;
}

export interface Resource {
  id: string;
  tenant_id: string;
  name: string;
  resource_type: ResourceType;
  description: string | null;
  capacity: number;
  status: ResourceStatus;
  amenities: string[];
  slot_duration_minutes: number;
  buffer_minutes: number;
}

export interface Reservation {
  id: string;
  tenant_id: string;
  resource_id: string;
  customer_id: string;
  reference_number: string;
  status: ReservationStatus;
  start_time: string;
  end_time: string;
  notes: string | null;
  cancellation_reason: string | null;
  confirmed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AvailableSlot {
  start_time: string;
  end_time: string;
  resource_id: string;
  duration_minutes: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiError {
  detail: string;
  errors?: Array<{ field: string; message: string; type: string }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
