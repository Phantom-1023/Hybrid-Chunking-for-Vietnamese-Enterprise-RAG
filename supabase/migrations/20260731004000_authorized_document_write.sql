-- Authoritative write gate for documents.  The caller remains the logged-in
-- user, while this function can safely inspect role and membership without a
-- recursive RLS policy evaluation.
create or replace function public.create_authorized_document(
  p_title text,
  p_content text,
  p_scope text,
  p_department_id uuid,
  p_owner_id uuid,
  p_source_name text default '',
  p_mime_type text default 'text/plain',
  p_storage_path text default '',
  p_checksum text default '',
  p_processing_status text default 'ready'
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  new_document_id uuid;
begin
  if auth.uid() is null or p_owner_id <> auth.uid() then
    raise exception 'Document owner must be the authenticated user' using errcode = '42501';
  end if;

  if not (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and is_active and role = 'admin'
    )
    or (
      p_scope <> 'organization'
      and exists (
        select 1 from public.department_memberships
        where user_id = auth.uid()
          and department_id = p_department_id
          and role = 'manager'
      )
    )
  ) then
    raise exception 'Not authorized to create this document' using errcode = '42501';
  end if;

  insert into public.documents (
    title, content, scope, department_id, owner_id, source_name,
    mime_type, storage_path, checksum, processing_status
  ) values (
    p_title, p_content, p_scope, p_department_id, p_owner_id, p_source_name,
    p_mime_type, p_storage_path, p_checksum, p_processing_status
  ) returning id into new_document_id;

  return new_document_id;
end;
$$;

revoke all on function public.create_authorized_document(
  text, text, text, uuid, uuid, text, text, text, text, text
) from public;
grant execute on function public.create_authorized_document(
  text, text, text, uuid, uuid, text, text, text, text, text
) to authenticated;
