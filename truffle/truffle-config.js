/**
 * Truffle project for SignGuard — lets the Ganache GUI add this as a WORKSPACE
 * and show the SignageRegistry contract, its transactions, and events.
 *
 * In the Ganache app:  New Workspace -> Add Project -> select this file.
 * The GUI's RPC server is usually http://127.0.0.1:7545 (see the app).
 */
module.exports = {
  networks: {
    // Ganache GUI default (workspace)
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*",
    },
    // Ganache CLI (if you use `ganache -p 8545` instead)
    cli: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*",
    },
  },
  compilers: {
    solc: {
      version: "0.8.19",
    },
  },
};
