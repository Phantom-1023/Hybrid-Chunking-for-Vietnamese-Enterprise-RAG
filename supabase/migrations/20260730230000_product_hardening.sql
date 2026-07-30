-- Product hardening V2: department membership, restricted documents,
-- citation-ready chunks, labels and a private source-file bucket.

create table if not exists public.department_memberships (
  department_id uuid not null references public.departments(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('manager', 'member')),
  created_at timestamptz not null default now(),
  primary key (department_id, user_id)
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  content text not null,
  locator text not null default '',
  chunk_index integer not null,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create table if not exists public.document_labels (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  color text not null default '#596780' check (color ~ '^#[0-9A-Fa-f]{6}$'),
  created_at timestamptz not null default now()
);

create table if not exists public.document_label_links (
  document_id uuid not null references public.documents(id) on delete cascade,
  label_id uuid not null references public.document_labels(id) on delete cascade,
  primary key (document_id, label_id)
);

create table if not exists public.document_access_grants (
  document_id uuid not null references public.documents(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (document_id, user_id)
);

alter table public.documents add column if not exists source_name text not null default '';
alter table public.documents add column if not exists mime_type text not null default 'text/plain';
alter table public.documents add column if not exists storage_path text not null default '';
alter table public.documents add column if not exists processing_status text not null default 'ready'
  check (processing_status in ('uploaded', 'processing', 'ready', 'failed'));
alter table public.documents add column if not exists checksum text not null default '';

insert into public.document_chunks (document_id, content, locator, chunk_index)
select d.id, d.content, 'Nội dung cũ', 0
from public.documents d
where d.content <> ''
  and not exists (
    select 1 from public.document_chunks c where c.document_id = d.id
  );

create or replace function public.is_department_manager(target_department uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.department_memberships
    where department_id = target_department and user_id = auth.uid() and role = 'manager'
  )
$$;

create or replace function public.can_access_document(target_document uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.documents d
    where d.id = target_document and (
      public.current_profile_role() = 'admin'
      or d.scope = 'organization'
      or d.owner_id = auth.uid()
      or (d.scope = 'department' and exists (
        select 1 from public.department_memberships m
        where m.department_id = d.department_id and m.user_id = auth.uid()
      ))
      or exists (
        select 1 from public.document_access_grants g
        where g.document_id = d.id and g.user_id = auth.uid()
      )
    )
  )
$$;

create or replace function public.can_edit_document(target_document uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.documents d
    where d.id = target_document and (
      public.current_profile_role() = 'admin'
      or (d.scope <> 'organization' and public.is_department_manager(d.department_id))
    )
  )
$$;

revoke all on function public.is_department_manager(uuid) from public;
revoke all on function public.can_access_document(uuid) from public;
revoke all on function public.can_edit_document(uuid) from public;
grant execute on function public.is_department_manager(uuid) to authenticated;
grant execute on function public.can_access_document(uuid) to authenticated;
grant execute on function public.can_edit_document(uuid) to authenticated;

alter table public.department_memberships enable row level security;
alter table public.document_chunks enable row level security;
alter table public.document_labels enable row level security;
alter table public.document_label_links enable row level security;
alter table public.document_access_grants enable row level security;

drop policy if exists department_memberships_read on public.department_memberships;
create policy department_memberships_read on public.department_memberships for select to authenticated
using (
  user_id = auth.uid()
  or public.current_profile_role() = 'admin'
  or public.is_department_manager(department_id)
);

drop policy if exists department_memberships_admin_write on public.department_memberships;
create policy department_memberships_admin_write on public.department_memberships for all to authenticated
using (
  public.current_profile_role() = 'admin'
  or public.is_department_manager(department_id)
)
with check (
  public.current_profile_role() = 'admin'
  or (public.is_department_manager(department_id) and role = 'member')
);

drop policy if exists document_chunks_read on public.document_chunks;
create policy document_chunks_read on public.document_chunks for select to authenticated
using (public.can_access_document(document_id));

drop policy if exists document_labels_read on public.document_labels;
create policy document_labels_read on public.document_labels for select to authenticated using (true);
drop policy if exists document_labels_admin_write on public.document_labels;
create policy document_labels_admin_write on public.document_labels for all to authenticated
using (public.current_profile_role() = 'admin') with check (public.current_profile_role() = 'admin');

drop policy if exists document_label_links_read on public.document_label_links;
create policy document_label_links_read on public.document_label_links for select to authenticated
using (public.can_access_document(document_id));

drop policy if exists document_access_grants_owner_read on public.document_access_grants;
create policy document_access_grants_owner_read on public.document_access_grants for select to authenticated
using (user_id = auth.uid() or public.can_edit_document(document_id));

drop policy if exists documents_read_acl on public.documents;
create policy documents_read_acl on public.documents for select to authenticated
using (public.can_access_document(id));

drop policy if exists documents_insert_acl on public.documents;
create policy documents_insert_acl on public.documents for insert to authenticated with check (
  owner_id = auth.uid() and (
    public.current_profile_role() = 'admin'
    or (scope <> 'organization' and public.is_department_manager(department_id))
  )
);

drop policy if exists documents_update_acl on public.documents;
create policy documents_update_acl on public.documents for update to authenticated
using (public.can_edit_document(id))
with check (
  public.current_profile_role() = 'admin'
  or (scope <> 'organization' and public.is_department_manager(department_id))
);

drop policy if exists documents_delete_acl on public.documents;
create policy documents_delete_acl on public.documents for delete to authenticated
using (public.can_edit_document(id));

insert into storage.buckets (id, name, public)
values ('enterprise-documents', 'enterprise-documents', false)
on conflict (id) do update set public = false;

drop policy if exists enterprise_documents_read on storage.objects;
create policy enterprise_documents_read on storage.objects for select to authenticated
using (
  bucket_id = 'enterprise-documents'
  and exists (
    select 1 from public.documents d
    where d.storage_path = name and public.can_access_document(d.id)
  )
);

create index if not exists department_memberships_user_idx on public.department_memberships(user_id);
create index if not exists document_chunks_document_idx on public.document_chunks(document_id, chunk_index);
create index if not exists document_access_grants_user_idx on public.document_access_grants(user_id);
