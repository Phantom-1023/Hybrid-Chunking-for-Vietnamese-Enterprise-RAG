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
  )
)
with check (
  public.current_profile_role() = 'admin'
  or (
    public.current_profile_role() = 'manager'
    and department_id = public.current_profile_department()
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
  )
);

drop policy if exists audit_insert on public.audit_logs;
create policy audit_insert on public.audit_logs
for insert to authenticated
with check (actor_id = auth.uid());

drop policy if exists audit_admin_read on public.audit_logs;
create policy audit_admin_read on public.audit_logs
for select to authenticated
using (public.current_profile_role() = 'admin');

create index if not exists documents_department_idx
  on public.documents(department_id);
create index if not exists documents_owner_idx
  on public.documents(owner_id);
create index if not exists audit_logs_actor_idx
  on public.audit_logs(actor_id);
