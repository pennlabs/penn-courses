/* eslint-disable no-console */
const express = require("express");
const next = require("next");

const devProxy = {
    "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
    },
    "/accounts": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
    },
};

const port = parseInt(process.env.PORT, 10) || 3000;
const env = process.env.NODE_ENV;
const dev = env !== "production";
const app = next({
    dir: ".", // base directory where everything is, could move to src later
    dev,
});

const handle = app.getRequestHandler();

let server;
app.prepare()
    .then(() => {
        server = express();

        if (dev) {
            server.on("upgrade", handle);

            // Set up the proxy.
            if (devProxy) {
                /* eslint-disable */
                const {
                    createProxyMiddleware,
                } = require("http-proxy-middleware");
                Object.keys(devProxy).forEach(function (context) {
                    server.use(
                        createProxyMiddleware(context, devProxy[context])
                    );
                });
                /* eslint-enable */
            }
        }

        // Default catch-all handler to allow Next.js to handle all other routes
        server.all("*", (req, res) => handle(req, res));

        server.listen(port, (err) => {
            if (err) {
                throw err;
            }
            console.log(`> Ready on port ${port} [${env || "development"}]`);
        });
    })
    .catch((err) => {
        console.log("An error occurred, unable to start the server");
        console.log(err);
    });
