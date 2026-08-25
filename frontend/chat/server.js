/* eslint-disable no-console */
const express = require("express");
const next = require("next");
const { createProxyMiddleware } = require("http-proxy-middleware");

/**
 * Next's built-in `rewrites` proxy gives up on an upstream request after 30 seconds
 * and returns a 500 ("socket hang up"). A chat turn can legitimately run longer than
 * that — the backend makes several tool calls and a model round trip for each — and
 * when it does, the request keeps running server-side while the browser is told it
 * failed. That is how you get a cart that changed with no reply to show for it.
 *
 * Proxying through express instead lets us set the timeout ourselves. It also passes
 * the path through verbatim, so Django's trailing slashes survive without the
 * `trailingSlash` juggling Next's rewrites needed.
 */
const PROXY_TIMEOUT_MS = 5 * 60 * 1000;

const devProxy = {
    "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        proxyTimeout: PROXY_TIMEOUT_MS,
        timeout: PROXY_TIMEOUT_MS,
    },
    "/accounts": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        proxyTimeout: PROXY_TIMEOUT_MS,
        timeout: PROXY_TIMEOUT_MS,
    },
};

const port = parseInt(process.env.PORT, 10) || 3001;
const env = process.env.NODE_ENV;
const dev = env !== "production";
const app = next({ dir: ".", dev });
const handle = app.getRequestHandler();

app.prepare()
    .then(() => {
        const server = express();

        if (dev) {
            server.on("upgrade", handle);
            Object.keys(devProxy).forEach((context) => {
                server.use(createProxyMiddleware(context, devProxy[context]));
            });
        }

        server.all("*", (req, res) => handle(req, res));

        server.listen(port, (err) => {
            if (err) throw err;
            console.log(`> Ready on port ${port} [${env || "development"}]`);
        });
    })
    .catch((err) => {
        console.log("An error occurred, unable to start the server");
        console.log(err);
    });
