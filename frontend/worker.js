const BACKEND = "https://homepassdemo.vercel.app";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api")) {
      return fetch(new Request(BACKEND + url.pathname + url.search, request));
    }
    return env.ASSETS.fetch(request);
  },
};