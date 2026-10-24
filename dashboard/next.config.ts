import type { NextConfig } from 'next';

// Static export: the dashboard is one page over public/counterfoil-data.json, so it can be hosted
// as plain files (Render static site, GitHub Pages) with no server and no credentials.
const nextConfig: NextConfig = { output: 'export' };

export default nextConfig;
