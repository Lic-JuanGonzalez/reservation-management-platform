"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-07 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums — separate execute calls (asyncpg rejects multi-statement strings)
    op.execute("DO $$ BEGIN CREATE TYPE business_type_enum AS ENUM ('hotel','medical_clinic','dental_office','gym','beauty_salon','coworking','event_venue','professional_services','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE tenant_status_enum AS ENUM ('active','suspended','cancelled','trial'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE user_role_enum AS ENUM ('super_admin','tenant_admin','employee','customer'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE user_status_enum AS ENUM ('active','inactive','pending_verification','suspended'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE resource_type_enum AS ENUM ('room','staff','equipment','space','service'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE resource_status_enum AS ENUM ('active','inactive','maintenance'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE reservation_status_enum AS ENUM ('pending','confirmed','cancelled','completed','no_show','waitlisted'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE rule_type_enum AS ENUM ('working_hours','holiday','maintenance','blackout','custom'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE notification_channel_enum AS ENUM ('email','sms','push'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE notification_status_enum AS ENUM ('pending','sent','failed','cancelled'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE notification_event_type_enum AS ENUM ('reservation_created','reservation_confirmed','reservation_cancelled','reservation_updated','reservation_reminder','email_verification','password_reset','welcome'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # Sequence for reference numbers
    op.execute("CREATE SEQUENCE IF NOT EXISTS reservation_reference_seq START 1000000")

    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("business_type", postgresql.ENUM(name="business_type_enum", create_type=False), nullable=False),
        sa.Column("owner_email", sa.String(255), nullable=False),
        sa.Column("status", postgresql.ENUM(name="tenant_status_enum", create_type=False), nullable=False, server_default="trial"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("uq_tenants_slug", "tenants", ["slug"], unique=True, schema="public")
    op.create_index("ix_tenants_status", "tenants", ["status"], schema="public")

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", postgresql.ENUM(name="user_role_enum", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM(name="user_status_enum", create_type=False), nullable=False, server_default="pending_verification"),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("phone_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notification_preferences", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("uq_users_email_tenant", "users", ["email", "tenant_id"], unique=True, schema="public")
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], schema="public")
    op.create_index("ix_users_email", "users", ["email"], schema="public")
    op.create_index("ix_users_role", "users", ["role"], schema="public")

    # resources
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("resource_type", postgresql.ENUM(name="resource_type_enum", create_type=False), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", postgresql.ENUM(name="resource_status_enum", create_type=False), nullable=False, server_default="active"),
        sa.Column("working_hours", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("amenities", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("image_urls", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("slot_duration_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("buffer_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("ix_resources_tenant_id", "resources", ["tenant_id"], schema="public")
    op.create_index("ix_resources_status", "resources", ["status"], schema="public")
    op.create_index("ix_resources_type", "resources", ["resource_type"], schema="public")

    # reservations
    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_number", sa.String(20), nullable=False),
        sa.Column("status", postgresql.ENUM(name="reservation_status_enum", create_type=False), nullable=False, server_default="pending"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("internal_notes", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("uq_reservations_reference_tenant", "reservations", ["reference_number", "tenant_id"], unique=True, schema="public")
    op.create_index("ix_reservations_tenant_id", "reservations", ["tenant_id"], schema="public")
    op.create_index("ix_reservations_resource_id", "reservations", ["resource_id"], schema="public")
    op.create_index("ix_reservations_customer_id", "reservations", ["customer_id"], schema="public")
    op.create_index("ix_reservations_status", "reservations", ["status"], schema="public")
    op.create_index("ix_reservations_start_time", "reservations", ["start_time"], schema="public")
    # Composite index for overlap detection (most critical query)
    op.create_index(
        "ix_reservations_overlap",
        "reservations",
        ["tenant_id", "resource_id", "start_time", "end_time", "status"],
        schema="public",
    )

    # availability_rules
    op.create_table(
        "availability_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.resources.id", ondelete="CASCADE"), nullable=True),
        sa.Column("rule_type", postgresql.ENUM(name="rule_type_enum", create_type=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("weekday", sa.Integer, nullable=True),
        sa.Column("start_time", sa.Time, nullable=True),
        sa.Column("end_time", sa.Time, nullable=True),
        sa.Column("specific_date", sa.Date, nullable=True),
        sa.Column("date_from", sa.Date, nullable=True),
        sa.Column("date_to", sa.Date, nullable=True),
        sa.Column("is_recurring", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("ix_avail_rules_tenant", "availability_rules", ["tenant_id"], schema="public")
    op.create_index("ix_avail_rules_resource", "availability_rules", ["resource_id"], schema="public")

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("public.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", postgresql.ENUM(name="notification_channel_enum", create_type=False), nullable=False),
        sa.Column("event_type", postgresql.ENUM(name="notification_event_type_enum", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM(name="notification_status_enum", create_type=False), nullable=False, server_default="pending"),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("template_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema="public",
    )
    op.create_index("ix_notifications_tenant", "notifications", ["tenant_id"], schema="public")
    op.create_index("ix_notifications_status", "notifications", ["status"], schema="public")

    # Enable Row-Level Security
    for table in ["tenants", "users", "resources", "reservations", "availability_rules", "notifications"]:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in ["notifications", "availability_rules", "reservations", "resources", "users", "tenants"]:
        op.drop_table(table, schema="public")

    op.execute("DROP SEQUENCE IF EXISTS reservation_reference_seq")

    for enum in [
        "notification_event_type_enum", "notification_status_enum", "notification_channel_enum",
        "rule_type_enum", "reservation_status_enum", "resource_status_enum", "resource_type_enum",
        "user_status_enum", "user_role_enum", "tenant_status_enum", "business_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
