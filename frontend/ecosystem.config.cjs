module.exports = {
  apps: [{
    name: 'kouper',
    script: 'build/index.js',
    interpreter: '/root/.nvm/versions/node/v20.20.1/bin/node',
    env: {
      NODE_ENV: 'production',
      PORT: '3002',
      ORIGIN: 'http://cc.tejitpabari.com',
      KOUPER_BASE: '/kouper',
    }
  }]
}
