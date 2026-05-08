/**
 * WxWords Cloud Upload API
 *
 * Cloudflare Worker that handles cloud photo uploads.
 * Images stored in R2, metadata as JSON alongside each image.
 *
 * Routes:
 *   POST /upload         - Upload image + metadata
 *   GET  /pending        - List pending submissions (admin only)
 *   POST /review/:id     - Approve/reject a submission (admin only)
 *   GET  /stats          - Public stats (total uploads, class counts)
 */

const VALID_CLASSES = [
  "Ac", "As", "Asperitas", "Cb", "Cc", "Ci", "Clear",
  "Cs", "Ct", "Cu", "Fog", "Lenticular", "Mammatus",
  "Ns", "Rainbow", "Sc", "St",
];

function corsHeaders(env, request) {
  const origin = request.headers.get("Origin") || "";
  // Allow both the production site and localhost for dev
  const allowed = [env.ALLOWED_ORIGIN, "http://localhost:8080", "http://127.0.0.1:8080"];
  const allow = allowed.includes(origin) ? origin : env.ALLOWED_ORIGIN;
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
  };
}

function isAdmin(request, env) {
  const auth = request.headers.get("Authorization") || "";
  if (auth.startsWith("Bearer ")) {
    return auth.slice(7) === env.ADMIN_TOKEN;
  }
  // Also check cookie
  const cookies = request.headers.get("Cookie") || "";
  const match = cookies.match(/wxwords_admin=([^;]+)/);
  return match && match[1] === env.ADMIN_TOKEN;
}

function jsonResponse(data, status, env, request) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(env, request) },
  });
}

function generateId() {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `${ts}-${rand}`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(env, request) });
    }

    try {
      if (url.pathname === "/upload" && request.method === "POST") {
        return handleUpload(request, env);
      }
      if (url.pathname === "/pending" && request.method === "GET") {
        return handlePending(request, env);
      }
      if (url.pathname.startsWith("/review/") && request.method === "POST") {
        return handleReview(request, env, url);
      }
      if (url.pathname === "/stats" && request.method === "GET") {
        return handleStats(request, env);
      }

      return jsonResponse({ error: "Not found" }, 404, env, request);
    } catch (e) {
      return jsonResponse({ error: e.message }, 500, env, request);
    }
  },
};

async function handleUpload(request, env) {
  const formData = await request.formData();
  const image = formData.get("image");
  const cloudClass = formData.get("cloud_class");
  const metadataRaw = formData.get("metadata");

  if (!image || !cloudClass) {
    return jsonResponse({ error: "Missing image or cloud_class" }, 400, env, request);
  }

  if (!VALID_CLASSES.includes(cloudClass)) {
    return jsonResponse({ error: `Invalid class: ${cloudClass}` }, 400, env, request);
  }

  // Validate image type
  if (!image.type || !image.type.match(/^image\/(jpeg|png)$/)) {
    return jsonResponse({ error: "Only JPEG and PNG images accepted" }, 400, env, request);
  }

  // Size limit: 10MB
  if (image.size > 10 * 1024 * 1024) {
    return jsonResponse({ error: "Image too large (max 10MB)" }, 400, env, request);
  }

  const admin = isAdmin(request, env);
  const id = generateId();
  const ext = image.type === "image/png" ? "png" : "jpg";
  const imageKey = `uploads/${id}.${ext}`;
  const metaKey = `uploads/${id}.json`;

  // Parse optional metadata
  let extra = {};
  if (metadataRaw) {
    try {
      extra = JSON.parse(metadataRaw);
    } catch {
      // Ignore parse errors
    }
  }

  const metadata = {
    id,
    cloud_class: cloudClass,
    status: admin ? "approved" : "pending",
    uploaded_at: new Date().toISOString(),
    image_key: imageKey,
    image_type: image.type,
    image_size: image.size,
    admin_upload: admin,
    ...extra,
  };

  // Store image and metadata in R2
  await env.BUCKET.put(imageKey, image.stream(), {
    httpMetadata: { contentType: image.type },
  });
  await env.BUCKET.put(metaKey, JSON.stringify(metadata, null, 2), {
    httpMetadata: { contentType: "application/json" },
  });

  return jsonResponse({
    success: true,
    id,
    status: metadata.status,
    message: admin
      ? "Upload approved automatically (admin)."
      : "Upload received and pending review. Thank you!",
  }, 200, env, request);
}

async function handlePending(request, env) {
  if (!isAdmin(request, env)) {
    return jsonResponse({ error: "Unauthorized" }, 401, env, request);
  }

  const list = await env.BUCKET.list({ prefix: "uploads/", delimiter: "/" });
  const pending = [];

  for (const obj of list.objects) {
    if (!obj.key.endsWith(".json")) continue;

    const metaObj = await env.BUCKET.get(obj.key);
    if (!metaObj) continue;

    const meta = await metaObj.json();
    if (meta.status === "pending") {
      pending.push(meta);
    }
  }

  // Sort newest first
  pending.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));

  return jsonResponse({ count: pending.length, items: pending }, 200, env, request);
}

async function handleReview(request, env, url) {
  if (!isAdmin(request, env)) {
    return jsonResponse({ error: "Unauthorized" }, 401, env, request);
  }

  const id = url.pathname.split("/review/")[1];
  if (!id) {
    return jsonResponse({ error: "Missing ID" }, 400, env, request);
  }

  const body = await request.json();
  const action = body.action; // "approve" or "reject"

  if (!["approve", "reject"].includes(action)) {
    return jsonResponse({ error: "Action must be 'approve' or 'reject'" }, 400, env, request);
  }

  const metaKey = `uploads/${id}.json`;
  const metaObj = await env.BUCKET.get(metaKey);
  if (!metaObj) {
    return jsonResponse({ error: "Not found" }, 404, env, request);
  }

  const meta = await metaObj.json();

  if (action === "reject") {
    // Delete image and metadata
    await env.BUCKET.delete(meta.image_key);
    await env.BUCKET.delete(metaKey);
    return jsonResponse({ success: true, action: "rejected", id }, 200, env, request);
  }

  // Approve — optionally reclassify
  meta.status = "approved";
  meta.reviewed_at = new Date().toISOString();
  if (body.cloud_class && VALID_CLASSES.includes(body.cloud_class)) {
    meta.original_class = meta.cloud_class;
    meta.cloud_class = body.cloud_class;
  }

  await env.BUCKET.put(metaKey, JSON.stringify(meta, null, 2), {
    httpMetadata: { contentType: "application/json" },
  });

  return jsonResponse({ success: true, action: "approved", id }, 200, env, request);
}

async function handleStats(request, env) {
  const list = await env.BUCKET.list({ prefix: "uploads/", delimiter: "/" });
  let total = 0;
  let approved = 0;
  let pending = 0;
  const classCounts = {};

  for (const obj of list.objects) {
    if (!obj.key.endsWith(".json")) continue;

    const metaObj = await env.BUCKET.get(obj.key);
    if (!metaObj) continue;

    const meta = await metaObj.json();
    total++;
    if (meta.status === "approved") {
      approved++;
      classCounts[meta.cloud_class] = (classCounts[meta.cloud_class] || 0) + 1;
    } else if (meta.status === "pending") {
      pending++;
    }
  }

  return jsonResponse({ total, approved, pending, classes: classCounts }, 200, env, request);
}
