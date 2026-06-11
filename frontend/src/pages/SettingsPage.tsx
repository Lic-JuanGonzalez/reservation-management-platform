import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";
import toast from "react-hot-toast";
import { tenantsApi, type TenantSettings } from "@/services/api/tenants";
import { useAuthStore } from "@/store/authStore";

const TIMEZONES = [
  "UTC", "America/Argentina/Buenos_Aires", "America/New_York", "America/Chicago",
  "America/Los_Angeles", "America/Sao_Paulo", "Europe/London", "Europe/Madrid",
  "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney",
];

const CURRENCIES = ["USD", "EUR", "ARS", "BRL", "GBP", "JPY", "MXN", "CLP", "COP"];
const LOCALES = ["en-US", "es-AR", "es-ES", "es-MX", "pt-BR", "fr-FR", "de-DE"];

export default function SettingsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const tenantId = user?.tenant_id;

  const { data: tenant, isLoading } = useQuery({
    queryKey: ["tenant", tenantId],
    queryFn: () => tenantsApi.get(tenantId!),
    enabled: !!tenantId,
  });

  const [form, setForm] = useState<Partial<TenantSettings>>({});
  const [tenantForm, setTenantForm] = useState({ name: "", phone: "", website: "", address: "" });

  useEffect(() => {
    if (tenant) {
      setForm(tenant.settings);
      setTenantForm({
        name: tenant.name,
        phone: tenant.phone ?? "",
        website: tenant.website ?? "",
        address: tenant.address ?? "",
      });
    }
  }, [tenant]);

  const settingsMutation = useMutation({
    mutationFn: (payload: Partial<TenantSettings>) => tenantsApi.updateSettings(tenantId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant", tenantId] });
      toast.success("Settings saved");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to save settings"),
  });

  const tenantMutation = useMutation({
    mutationFn: () => tenantsApi.update(tenantId!, {
      name: tenantForm.name,
      phone: tenantForm.phone || undefined,
      website: tenantForm.website || undefined,
      address: tenantForm.address || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant", tenantId] });
      toast.success("Profile saved");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to save profile"),
  });

  const set = <K extends keyof TenantSettings>(key: K, value: TenantSettings[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  if (!tenantId) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Settings are only available for tenant accounts.</p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-6 text-center text-gray-400">Loading...</div>;
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>

      {/* Business profile */}
      <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white">Business Profile</h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Business Name">
            <input value={tenantForm.name} onChange={(e) => setTenantForm((f) => ({ ...f, name: e.target.value }))}
              className={inputCls} />
          </Field>
          <Field label="Phone">
            <input value={tenantForm.phone} onChange={(e) => setTenantForm((f) => ({ ...f, phone: e.target.value }))}
              className={inputCls} />
          </Field>
          <Field label="Website">
            <input value={tenantForm.website} onChange={(e) => setTenantForm((f) => ({ ...f, website: e.target.value }))}
              className={inputCls} />
          </Field>
          <Field label="Address">
            <input value={tenantForm.address} onChange={(e) => setTenantForm((f) => ({ ...f, address: e.target.value }))}
              className={inputCls} />
          </Field>
        </div>
        <div className="flex justify-end">
          <SaveButton isPending={tenantMutation.isPending} onClick={() => tenantMutation.mutate()} />
        </div>
      </section>

      {/* Localization */}
      <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white">Localization</h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Timezone">
            <select value={form.timezone ?? ""} onChange={(e) => set("timezone", e.target.value)} className={inputCls}>
              {TIMEZONES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Locale">
            <select value={form.locale ?? ""} onChange={(e) => set("locale", e.target.value)} className={inputCls}>
              {LOCALES.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </Field>
          <Field label="Currency">
            <select value={form.currency ?? ""} onChange={(e) => set("currency", e.target.value)} className={inputCls}>
              {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
        </div>
      </section>

      {/* Booking rules */}
      <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white">Booking Rules</h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Max advance booking (days)" hint="1–365">
            <input type="number" min={1} max={365} value={form.max_advance_booking_days ?? ""}
              onChange={(e) => set("max_advance_booking_days", Number(e.target.value))} className={inputCls} />
          </Field>
          <Field label="Min advance booking (hours)" hint="0–720">
            <input type="number" min={0} max={720} value={form.min_advance_booking_hours ?? ""}
              onChange={(e) => set("min_advance_booking_hours", Number(e.target.value))} className={inputCls} />
          </Field>
          <Field label="Max reservations per customer" hint="1–100">
            <input type="number" min={1} max={100} value={form.max_reservations_per_customer ?? ""}
              onChange={(e) => set("max_reservations_per_customer", Number(e.target.value))} className={inputCls} />
          </Field>
          <Field label="Cancellation window (hours)" hint="0–720">
            <input type="number" min={0} max={720} value={form.cancellation_hours_before ?? ""}
              onChange={(e) => set("cancellation_hours_before", Number(e.target.value))} className={inputCls} />
          </Field>
          <Field label="Slot duration (minutes)" hint="15–480">
            <input type="number" min={15} max={480} step={15} value={form.slot_duration_minutes ?? ""}
              onChange={(e) => set("slot_duration_minutes", Number(e.target.value))} className={inputCls} />
          </Field>
        </div>

        {/* Toggles */}
        <div className="space-y-3 pt-2">
          <Toggle
            label="Require email verification"
            checked={!!form.require_email_verification}
            onChange={(v) => set("require_email_verification", v)}
          />
          <Toggle
            label="Allow guest bookings"
            checked={!!form.allow_guest_bookings}
            onChange={(v) => set("allow_guest_bookings", v)}
          />
          <Toggle
            label="Send reminders"
            checked={!!form.send_reminders}
            onChange={(v) => set("send_reminders", v)}
          />
        </div>

        <div className="flex justify-end">
          <SaveButton isPending={settingsMutation.isPending} onClick={() => settingsMutation.mutate(form)} />
        </div>
      </section>
    </div>
  );
}

const inputCls =
  "w-full px-3.5 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}{hint && <span className="text-gray-400 font-normal ml-1 text-xs">({hint})</span>}
      </label>
      {children}
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer">
      <div
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-5 rounded-full transition-colors ${checked ? "bg-indigo-600" : "bg-gray-300 dark:bg-gray-600"}`}
      >
        <div className={`absolute top-0.5 left-0.5 h-4 w-4 bg-white rounded-full shadow transition-transform ${checked ? "translate-x-5" : ""}`} />
      </div>
      <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
    </label>
  );
}

function SaveButton({ isPending, onClick }: { isPending: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={isPending}
      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors"
    >
      {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
      {isPending ? "Saving..." : "Save"}
    </button>
  );
}
