const proxy = require("http-proxy-middleware");

module.exports = function(app) {
  const proxyUrl = process.env.PROXY_URL || "http://127.0.0.1:8000";
  app.use(
    proxy("/api", {
      logLevel: "debug",
      target: proxyUrl,
      changeOrigin: true,
      secure: false
    })
  );
  app.use(
    proxy("/accounts", {
      logLevel: "debug",
      target: proxyUrl,
      changeOrigin: true,
      secure: false
    })
  );
};
