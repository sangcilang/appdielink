import { handleUpload } from '@vercel/blob/client';

const BACKEND_API_URL = process.env.BACKEND_API_URL;

export async function POST(request) {
  const body = await request.json();

  try {
    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async (pathname, clientPayload) => {
        if (!BACKEND_API_URL) {
          throw new Error('Missing BACKEND_API_URL');
        }

        const parsed = clientPayload ? JSON.parse(clientPayload) : {};
        const token = parsed?.token;
        if (!token) {
          throw new Error('Unauthorized');
        }

        // Verify token with backend and fetch user id for scoping the upload path.
        const meRes = await fetch(`${BACKEND_API_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!meRes.ok) {
          throw new Error('Unauthorized');
        }
        const me = await meRes.json();
        const userId = me?.id;

        if (!userId || typeof userId !== 'string') {
          throw new Error('Unauthorized');
        }

        if (!String(pathname).startsWith(`uploads/${userId}/`)) {
          throw new Error('Invalid pathname');
        }

        return {
          access: 'private',
          addRandomSuffix: true,
          tokenPayload: JSON.stringify({ userId }),
        };
      },
      onUploadCompleted: async () => {
        // We register the blob URL from the client after upload finishes.
      },
    });

    return Response.json(jsonResponse);
  } catch (error) {
    return Response.json(
      { error: error?.message || 'Upload token error' },
      { status: 400 },
    );
  }
}
