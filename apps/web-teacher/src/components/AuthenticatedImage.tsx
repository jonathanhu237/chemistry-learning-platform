import { useEffect, useState } from "react";

import { getAuthToken } from "../api/auth";

export function AuthenticatedImage({ src, alt, className }: { src?: string | null; alt: string; className?: string }) {
  const [objectUrl, setObjectUrl] = useState<string>();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let nextUrl: string | undefined;
    setObjectUrl(undefined);
    setFailed(false);
    if (!src) return undefined;
    const headers = new Headers();
    const token = getAuthToken();
    if (token) headers.set("Authorization", "Bearer " + token);
    void fetch(src, { headers })
      .then((response) => {
        if (!response.ok) throw new Error("image_load_failed");
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        nextUrl = URL.createObjectURL(blob);
        setObjectUrl(nextUrl);
      })
      .catch(() => {
        if (!cancelled) {
          setObjectUrl(undefined);
          setFailed(true);
        }
      });
    return () => {
      cancelled = true;
      if (nextUrl) URL.revokeObjectURL(nextUrl);
    };
  }, [src]);

  return objectUrl && !failed ? (
    <img
      src={objectUrl}
      alt={alt}
      className={className}
      onError={() => {
        setObjectUrl(undefined);
        setFailed(true);
      }}
    />
  ) : null;
}
