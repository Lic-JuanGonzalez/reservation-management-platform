import { apiClient } from "./client";

export interface DailyReport {
  date: string;
  total: number;
  confirmed: number;
  cancelled: number;
  pending: number;
  completed: number;
}

export interface SummaryReport {
  period_start: string;
  period_end: string;
  total_reservations: number;
  confirmed: number;
  cancelled: number;
  completed: number;
  cancellation_rate: number;
}

export const reportsApi = {
  daily: (start_date: string, end_date: string) =>
    apiClient
      .get<DailyReport[]>("/reports/daily", { params: { start_date, end_date } })
      .then((r) => r.data),

  summary: (start_date: string, end_date: string) =>
    apiClient
      .get<SummaryReport>("/reports/summary", { params: { start_date, end_date } })
      .then((r) => r.data),
};
