const NodeMediaServer = require('node-media-server');

const config = {
  rtmp: {
    port: 1935,
    chunk_size: 60000,
    gop_cache: true,
    ping: 30,
    ping_timeout: 60
  },
  https: {
    port: 8443,
    key:'/etc/nginx/ssl/live.sportshub.info/fullchain.pem',
    cert:'/etc/nginx/ssl/live.sportshub.info/key.pem',
    allow_origin: '*'
    mediaroot: '/mnt/ramdisk/rmtp-server/media'
  }
};

var nms = new NodeMediaServer(config)
nms.run();
