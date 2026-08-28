create or replace function public.claim_render_jobs(p_limit integer default 1)
returns setof public.render_jobs
language plpgsql
security definer
set search_path = ''
as $$
begin
  return query
  with picked as (
    select id
    from public.render_jobs
    where status = 'queued'
    order by created_at
    for update skip locked
    limit greatest(1, least(coalesce(p_limit, 1), 8))
  )
  update public.render_jobs j
     set status = 'processing',
         progress = greatest(j.progress, 1),
         started_at = coalesce(j.started_at, now()),
         updated_at = now(),
         engine = 'ffmpeg-worker'
    from picked
   where j.id = picked.id
  returning j.*;
end;
$$;

revoke all on function public.claim_render_jobs(integer) from public, anon, authenticated;
grant execute on function public.claim_render_jobs(integer) to service_role;

create index if not exists idx_render_jobs_claim on public.render_jobs(status, created_at);
