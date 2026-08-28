-- Private Storage for AI Editor OS assets.
insert into storage.buckets (id, name, public)
values ('ai-editor-assets', 'ai-editor-assets', false)
on conflict (id) do update set public = false;

drop policy if exists ai_editor_assets_select on storage.objects;
create policy ai_editor_assets_select
on storage.objects for select to authenticated
using (
  bucket_id = 'ai-editor-assets'
  and exists (
    select 1
    from public.assets a
    join public.workspace_members wm on wm.workspace_id = a.workspace_id
    where a.storage_path = name
      and wm.user_id = (select auth.uid())
  )
);

drop policy if exists ai_editor_assets_insert on storage.objects;
create policy ai_editor_assets_insert
on storage.objects for insert to authenticated
with check (
  bucket_id = 'ai-editor-assets'
  and exists (
    select 1
    from public.workspace_members wm
    where wm.workspace_id::text = split_part(name, '/', 1)
      and wm.user_id = (select auth.uid())
  )
);

drop policy if exists ai_editor_assets_update on storage.objects;
create policy ai_editor_assets_update
on storage.objects for update to authenticated
using (
  bucket_id = 'ai-editor-assets'
  and exists (
    select 1
    from public.assets a
    join public.workspace_members wm on wm.workspace_id = a.workspace_id
    where a.storage_path = name
      and wm.user_id = (select auth.uid())
  )
)
with check (
  bucket_id = 'ai-editor-assets'
  and exists (
    select 1
    from public.workspace_members wm
    where wm.workspace_id::text = split_part(name, '/', 1)
      and wm.user_id = (select auth.uid())
  )
);

drop policy if exists ai_editor_assets_delete on storage.objects;
create policy ai_editor_assets_delete
on storage.objects for delete to authenticated
using (
  bucket_id = 'ai-editor-assets'
  and exists (
    select 1
    from public.assets a
    join public.workspace_members wm on wm.workspace_id = a.workspace_id
    where a.storage_path = name
      and wm.user_id = (select auth.uid())
  )
);
