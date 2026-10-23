const SignageRegistry = artifacts.require("SignageRegistry");

module.exports = function (deployer) {
  deployer.deploy(SignageRegistry);
};
