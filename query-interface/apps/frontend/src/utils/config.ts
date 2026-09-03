interface RuntimeConfig {
  lodviewUrl: string;
  sparqlEndpointUrl: string;
}

const DEFAULT_CONFIG: RuntimeConfig = {
  lodviewUrl: 'http://localhost:8082',
  sparqlEndpointUrl: 'http://localhost:8081',
};

let configPromise: Promise<RuntimeConfig> | null = null;

// `/query-interface/config.json` is written at container start by the
// `runtime-config.json` compose config (see query-interface/docker-compose.yml)
// so the same built image can point at a different LodView instance per
// environment. In local dev (rsbuild dev server, no static-web-server in
// front) the file doesn't exist, so we fall back to DEFAULT_CONFIG.
export function getRuntimeConfig(): Promise<RuntimeConfig> {
  if (!configPromise) {
    configPromise = fetch('/query-interface/config.json')
      .then((response) => {
        if (!response.ok) throw new Error(`status ${response.status}`);
        return response.json() as Promise<RuntimeConfig>;
      })
      .catch(() => DEFAULT_CONFIG);
  }
  return configPromise;
}
