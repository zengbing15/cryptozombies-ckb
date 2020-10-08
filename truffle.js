const HDWalletProvider = require("truffle-hdwallet-provider");

// Set your own mnemonic here
const mnemonic = "grain cart first tuition piano this light orient physical coin clinic guilt";

// Module exports to make this configuration available to Truffle itself
module.exports = {
  // Object with configuration for each network
  networks: {
    // Configuration for mainnet
    mainnet: {
      provider: function () {
        // Setting the provider with the Infura Rinkeby address and Token
        return new HDWalletProvider(mnemonic, "https://mainnet.infura.io/v3/YOUR_TOKEN")
      },
      network_id: "1"
    },
    // Configuration for rinkeby network
    rinkeby: {
      // Special function to setup the provider
      provider: function () {
        // Setting the provider with the Infura Rinkeby address and Token
        return new HDWalletProvider(mnemonic, "https://rinkeby.infura.io/v3/75f591cacd2c4dc78fa1cdfba482b178")
      },
      network_id: 4
    }
  }
}; 