module.exports = function override(config, env) {
    // Add a rule to handle .mjs files
    config.module.rules.push({
        test: /\.mjs$/,
        include: /node_modules/,
        type: 'javascript/auto',
    });

    return config;
};