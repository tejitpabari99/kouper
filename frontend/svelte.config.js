import adapter from '@sveltejs/adapter-node';

const base = process.env.KOUPER_BASE || '';

const config = {
  kit: {
    adapter: adapter(),
    paths: { base }
  }
};

export default config;
