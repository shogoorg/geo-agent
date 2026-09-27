/*
 Copyright 2026 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiKey = env.GOOGLE_MAPS_API_KEY || process.env.GOOGLE_MAPS_API_KEY || "$GOOGLE_MAPS_API_KEY"
  const serverUrl = env.SERVER_URL || process.env.SERVER_URL || "http://localhost:10002"

  return {
    base: './',
    // Added: Expose GOOGLE_MAPS_API_KEY to Vite client-side code for Google Maps Embed iframe
    define: {
      'import.meta.env.VITE_GOOGLE_MAPS_API_KEY': JSON.stringify(apiKey),
    },
    plugins: [
      react(),
      {
        name: "html-transform",
        transformIndexHtml(html) {
          return html.replace(
            "$GOOGLE_MAPS_API_KEY",
            apiKey
          ).replace(
            "$SERVER_URL",
            serverUrl
          );
        },
      }
    ],
  }
})
