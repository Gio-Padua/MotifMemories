import { createClient } from 'npm:@supabase/supabase-js@2'

const bucket = 'photobooth-testloc'
const boothIds = (Deno.env.get('BOOTH_IDS') ?? 'booth-001').split(',').map((value) => value.trim())
const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)

Deno.serve(async (request) => {
  if (request.headers.get('authorization') !== `Bearer ${Deno.env.get('CLEANUP_SECRET')}`) {
    return new Response('Unauthorized', { status: 401 })
  }

  const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000
  let deleted = 0
  for (const boothId of boothIds) {
    const prefix = `booths/${boothId}/results`
    for (;;) {
      const { data, error } = await supabase.storage.from(bucket).list(prefix, {
        limit: 100,
        sortBy: { column: 'created_at', order: 'asc' },
      })
      if (error) return Response.json({ error: error.message }, { status: 500 })
      const expired = data.filter((item) => item.created_at && Date.parse(item.created_at) < cutoff).map((item) => `${prefix}/${item.name}`)
      if (!expired.length) break
      const { error: deleteError } = await supabase.storage.from(bucket).remove(expired)
      if (deleteError) return Response.json({ error: deleteError.message }, { status: 500 })
      deleted += expired.length
    }
  }
  return Response.json({ deleted })
})
