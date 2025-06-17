const Immudb = require('immudb-node');

const { default: ImmudbClient } = require('immudb-node'); 

const cfg = { address: 'immudb:3322', rootPath: '.' };

const ready = (async () => {
  const client = new ImmudbClient(cfg);
  await client.login({ user: 'immudb', password: 'immudb' });
  console.log('🔗  immudb connected');
  return client;                              
})();


module.exports = async () => ready;

