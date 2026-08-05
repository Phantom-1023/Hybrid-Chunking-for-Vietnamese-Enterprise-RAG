-- Semi-ver1.00: preserve the purpose shown when an admin creates a department.
alter table public.departments
  add column if not exists description text not null default '';

