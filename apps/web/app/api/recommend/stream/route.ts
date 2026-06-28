// Server-side proxy for the FastAPI SSE stream. Keeps API_URL off the browser
// and avoids CORS — the client fetches this same-origin route, which forwards to
// the backend and pipes the event stream straight back.

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

export async function POST(req: Request): Promise<Response> {
  const body = await req.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/api/v1/recommend/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      cache: "no-store",
    });
  } catch {
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: "Could not reach the recommendation service." })}\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } },
    );
  }

  if (!upstream.ok || !upstream.body) {
    const detail = await upstream.text().catch(() => "");
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: detail || `API error ${upstream.status}` })}\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } },
    );
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
