import '@/styles/globals.css'
import { inter } from "@/fonts";
import type { AppProps } from 'next/app'
import React from 'react';


function App({ Component, pageProps }: AppProps) {
  return (
    <main className={inter.className}>
      <Component {...pageProps} />
    </main>
  )
}

export default App
