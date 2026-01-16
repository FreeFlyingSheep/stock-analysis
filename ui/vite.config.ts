import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "APP_");
    const host = env.BACKEND_HOST ?? "localhost";
    const port = env.BACKEND_PORT ?? "8000";

    return {
        plugins: [sveltekit()],
        server: {
            proxy: {
                "/api": {
                    target: `http://${host}:${port}`,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ""),
                },
            },
        },
    };
});
