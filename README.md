# cryptozombies-ckb

* Install node: v10.12.0
* npm install -g truffle
* npm install -g http-server
* 配置 web3
	* yarn add web3
	* index.html: <script src="https://unpkg.com/web3@latest/dist/web3.min.js"></script> 
* 启动 ganache
* 配置 metamask
 * 下载 chrome 插件
 * Get startted 
 * 输入 ganache 的 mnemonic
 * Custome RPC
 		* RPC URL: HTTP://127.0.0.1:7545 chain ID: 0x539
* truffle migrate
* 添加 index.html 中 CONTRACT_ADDRESS
* http-server
* 访问 http://127.0.0.1:8080 , 在控制台输入：
	* Create zombies: createRandomZombie("SOME NAME")
* Tips:
    * Uncaught (in promise) Error: No "from" address specified in neither the given options, nor the default options.
    at Object.ContractNoFromAddressDefinedError (errors.js:125)
    at Object.d._executeMethod (index.js:773)
    at createRandomZombie ((index):67)
    at <anonymous>:1:1
        * metamask 问题：https://stackoverflow.com/questions/56383938/no-valid-from-address-specified-in-neither-the-given-options-nor-the-default
        * 修改 index.html 中的代码：web3js = new Web3(web3.currentProvider.**enable()**), metamask 弹出后，再删除


