-- Enterprise RAG managed persistence.
-- Safe to re-run: schema objects use IF NOT EXISTS; policies are replaced.

create extension if not exists pgcrypto;

create table if not exists public.departments (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text not null default '',
  role text not null default 'member'
    check (role in ('admin', 'manager', 'member')),
  department_id uuid references public.departments(id) on delete set null,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  content text not null,
  scope text not null default 'department'
    check (scope in ('organization', 'department', 'private')),
  department_id uuid references public.departments(id) on delete set null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id) on delete set null,
  action text not null,
  resource_type text not null,
  resource_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.profiles
  add column if not exists is_active boolean not null default true;

do $$
begin
  alter table public.documents
    add constraint documents_scope_department_consistency
    check (
      (scope = 'organization' and department_id is null)
      or (scope = 'department' and department_id is not null)
      or scope = 'private'
    );
exception
  when duplicate_object then null;
end;
$$;

create or replace function public.current_profile_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where id = auth.uid()
$$;

create or replace function public.current_profile_department()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select department_id from public.profiles where id = auth.uid()
$$;

revoke all on function public.current_profile_role() from public;
revoke all on function public.current_profile_department() from public;
grant execute on function public.current_profile_role() to authenticated;
grant execute on function public.current_profile_department() to authenticated;

create or replace function public.bootstrap_admin_profile(
  target_user_id uuid,
  target_email text,
  target_display_name text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  perform pg_advisory_xact_lock(20260730);
  if exists (select 1 from public.profiles) then
    raise exception 'Admin bootstrap already completed';
  end if;
  insert into public.profiles (id, email, display_name, role)
  values (target_user_id, target_email, target_display_name, 'admin');
end;
$$;

revoke all on function public.bootstrap_admin_profile(uuid, text, text) from public;
revoke all on function public.bootstrap_admin_profile(uuid, text, text) from authenticated;
grant execute on function public.bootstrap_admin_profile(uuid, text, text) to service_role;

create or replace function public.append_audit_event(
  event_action text,
  event_resource_type text,
  event_resource_id text default null,
  event_outcome text default 'allowed',
  event_detail text default ''
)
returns void
language sql
security definer
set search_path = public
as $$
  insert into public.audit_logs (
    actor_id,
    action,
    resource_type,
    resource_id,
    metadata
  )
  values (
    auth.uid(),
    left(event_action, 100),
    left(event_resource_type, 100),
    event_resource_id,
    jsonb_build_object(
      'outcome', left(event_outcome, 100),
      'detail', left(event_detail, 500)
    )
  )
$$;

revoke all on function public.append_audit_event(text, text, text, text, text)
  from public;
grant execute on function public.append_audit_event(text, text, text, text, text)
  to authenticated;

alter table public.departments enable row level security;
alter table public.profiles enable row level security;
alter table public.documents enable row level security;
alter table public.audit_logs enable row level security;

drop policy if exists departments_read on public.departments;
create policy departments_read on public.departments
for select to authenticated using (true);

drop policy if exists departments_admin_write on public.departments;
create policy departments_admin_write on public.departments
for all to authenticated
using (public.current_profile_role() = 'admin')
with check (public.current_profile_role() = 'admin');

drop policy if exists profiles_read on public.profiles;
create policy profiles_read on public.profiles
for select to authenticated
using (id = auth.uid() or public.current_profile_role() = 'admin');

drop policy if exists profiles_admin_write on public.profiles;
create policy profiles_admin_write on public.profiles
for all to authenticated
using (public.current_profile_role() = 'admin')
with check (public.current_profile_role() = 'admin');

drop policy if exists documents_read_acl on public.documents;
create policy documents_read_acl on public.documents
for select to authenticated
using (
  public.current_profile_role() = 'admin'
  or scope = 'organization'
  or owner_id = auth.uid()
  or (
    scope = 'department'
    and department_id = public.current_profile_department()
  )
);

drop policy if exists documents_insert_acl on public.documents;
create policy documents_insert_acl on public.documents
for insert to authenticated
with check (
  owner_id = auth.uid()
  and (
    public.current_profile_role() = 'admin'
    or (
      public.current_profile_role() = 'manager'
      and department_id = public.current_profile_department()
      and scope <> 'organization'
    )
  )
);

drop policy if exists documents_update_acl on public.documents;
create policy documents_update_acl on public.documents
for update to authenticated
using (
  public.current_profile_role() = 'admin'
  or (
    public.current_profile_role() = 'manager'
    and department_id = public.current_profile_department()
    and owner_id = auth.uid()
  )
)
with check (
  public.current_profile_role() = 'admin'
  or (
    public.current_profile_role() = 'manager'
    and department_id = public.current_profile_department()
    and owner_id = auth.uid()
    and scope <> 'organization'
  )
);

drop policy if exists documents_delete_acl on public.documents;
create policy documents_delete_acl on public.documents
for delete to authenticated
using (
  public.current_profile_role() = 'admin'
  or (
    public.current_profile_role() = 'manager'
    and department_id = public.current_profile_department()
    and owner_id = auth.uid()
  )
);

drop policy if exists audit_insert on public.audit_logs;

drop policy if exists audit_admin_read on public.audit_logs;
create policy audit_admin_read on public.audit_logs
for select to authenticated
using (public.current_profile_role() = 'admin');

revoke all on public.departments, public.profiles, public.documents,
  public.audit_logs from anon;
revoke all on public.audit_logs from authenticated;
grant select on public.departments, public.profiles, public.documents
  to authenticated;
grant insert, update, delete on public.departments, public.profiles,
  public.documents to authenticated;
grant select on public.audit_logs to authenticated;

create index if not exists documents_department_idx
  on public.documents(department_id);
create index if not exists documents_owner_idx
  on public.documents(owner_id);
create index if not exists audit_logs_actor_idx
  on public.audit_logs(actor_id);
