-- AI Editor OS: multi-tenant SaaS foundation
create extension if not exists pgcrypto;

create type public.workspace_role as enum ('owner','admin','editor','viewer');
create type public.project_status as enum ('draft','analyzing','ready','rendering','completed','failed');
create type public.job_status as enum ('queued','processing','completed','failed','cancelled');

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  owner_id uuid not null references auth.users(id) on delete cascade,
  plan text not null default 'starter' check (plan in ('starter','pro','agency','enterprise')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.workspace_role not null default 'viewer',
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  created_by uuid not null references auth.users(id) on delete restrict,
  name text not null,
  status public.project_status not null default 'draft',
  settings jsonb not null default '{}'::jsonb,
  edit_plan jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.assets (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  kind text not null check (kind in ('video','image','audio','broll','thumbnail','render')),
  storage_path text not null,
  original_name text,
  mime_type text,
  size_bytes bigint,
  duration_seconds numeric,
  width int,
  height int,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.skills (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  name text not null,
  slug text not null,
  description text,
  rules jsonb not null default '{}'::jsonb,
  version int not null default 1,
  is_public boolean not null default false,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  asset_id uuid references public.assets(id) on delete cascade,
  transcript jsonb not null default '{}'::jsonb,
  scenes jsonb not null default '[]'::jsonb,
  vision jsonb not null default '{}'::jsonb,
  scores jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  created_by uuid not null references auth.users(id) on delete restrict,
  status public.job_status not null default 'queued',
  progress int not null default 0 check (progress between 0 and 100),
  engine text not null default 'render-adapter',
  payload jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.usage_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  event_type text not null,
  quantity numeric not null default 1,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_workspace_members_user on public.workspace_members(user_id);
create index if not exists idx_projects_workspace on public.projects(workspace_id, updated_at desc);
create index if not exists idx_assets_project on public.assets(project_id, created_at desc);
create index if not exists idx_jobs_project on public.render_jobs(project_id, created_at desc);
create index if not exists idx_jobs_status on public.render_jobs(status, created_at);

create or replace function public.is_workspace_member(p_workspace uuid)
returns boolean language sql stable security invoker as $$
  select exists(select 1 from public.workspace_members wm where wm.workspace_id = p_workspace and wm.user_id = auth.uid());
$$;

create or replace function public.is_workspace_admin(p_workspace uuid)
returns boolean language sql stable security invoker as $$
  select exists(select 1 from public.workspace_members wm where wm.workspace_id = p_workspace and wm.user_id = auth.uid() and wm.role in ('owner','admin'));
$$;

create or replace function public.create_ai_editor_project(p_name text, p_settings jsonb default '{}'::jsonb)
returns json language plpgsql security invoker as $$
declare
  ws uuid;
  result json;
begin
  select workspace_id into ws from public.workspace_members where user_id = auth.uid() order by created_at limit 1;
  if ws is null then
    insert into public.workspaces(name, slug, owner_id)
    values ('Workspace của tôi', 'ws-' || substr(replace(gen_random_uuid()::text,'-',''),1,12), auth.uid())
    returning id into ws;
    insert into public.workspace_members(workspace_id,user_id,role) values (ws, auth.uid(), 'owner');
  end if;
  insert into public.projects(workspace_id, created_by, name, settings)
  values (ws, auth.uid(), coalesce(nullif(trim(p_name),''),'AI Video Project'), coalesce(p_settings,'{}'::jsonb))
  returning to_jsonb(public.projects.*) into result;
  return result;
end;
$$;

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.projects enable row level security;
alter table public.assets enable row level security;
alter table public.skills enable row level security;
alter table public.analyses enable row level security;
alter table public.render_jobs enable row level security;
alter table public.usage_events enable row level security;

drop policy if exists workspaces_member_select on public.workspaces;
create policy workspaces_member_select on public.workspaces for select to authenticated using (public.is_workspace_member(id));
drop policy if exists workspaces_owner_insert on public.workspaces;
create policy workspaces_owner_insert on public.workspaces for insert to authenticated with check (owner_id = auth.uid());

drop policy if exists workspace_members_self on public.workspace_members;
create policy workspace_members_self on public.workspace_members for select to authenticated using (user_id = auth.uid() or public.is_workspace_member(workspace_id));
drop policy if exists workspace_members_owner_insert on public.workspace_members;
create policy workspace_members_owner_insert on public.workspace_members for insert to authenticated with check (user_id = auth.uid() and role = 'owner' and exists(select 1 from public.workspaces w where w.id = workspace_id and w.owner_id = auth.uid()));

drop policy if exists projects_member_all on public.projects;
create policy projects_member_all on public.projects for all to authenticated using (public.is_workspace_member(workspace_id)) with check (public.is_workspace_member(workspace_id));

drop policy if exists assets_member_all on public.assets;
create policy assets_member_all on public.assets for all to authenticated using (public.is_workspace_member(workspace_id)) with check (public.is_workspace_member(workspace_id));

drop policy if exists skills_member_all on public.skills;
create policy skills_member_all on public.skills for all to authenticated using (workspace_id is null or public.is_workspace_member(workspace_id)) with check (workspace_id is null or public.is_workspace_member(workspace_id));

drop policy if exists analyses_member_all on public.analyses;
create policy analyses_member_all on public.analyses for all to authenticated using (exists(select 1 from public.projects p where p.id = project_id and public.is_workspace_member(p.workspace_id))) with check (exists(select 1 from public.projects p where p.id = project_id and public.is_workspace_member(p.workspace_id)));

drop policy if exists jobs_member_all on public.render_jobs;
create policy jobs_member_all on public.render_jobs for all to authenticated using (public.is_workspace_member(workspace_id)) with check (public.is_workspace_member(workspace_id));

drop policy if exists usage_member_select on public.usage_events;
create policy usage_member_select on public.usage_events for select to authenticated using (public.is_workspace_member(workspace_id));
drop policy if exists usage_member_insert on public.usage_events;
create policy usage_member_insert on public.usage_events for insert to authenticated with check (public.is_workspace_member(workspace_id) and user_id = auth.uid());

grant execute on function public.create_ai_editor_project(text,jsonb) to authenticated;

alter publication supabase_realtime add table public.render_jobs;
