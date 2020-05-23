const getYarnWorkspaces = require('get-yarn-workspaces');
const { override, babelInclude } = require('customize-cra');

module.exports = override(
  babelInclude(getYarnWorkspaces())
);
