import { Html, Head, Main, NextScript } from 'next/document'
import React from 'react';

export default function Document() {
      return (
        <Html lang="en" style={{backgroundColor:'#F7F9FC'}}>
          <Head>
            <meta name="description" content="Penn Degree Plan by Penn Labs" />
            <link
                rel="stylesheet"
                href="https://use.fontawesome.com/releases/v5.6.3/css/all.css"
                integrity="sha384-UHRtZLI+pbxtHCWp1t77Bi1L4ZtiqrqD80Kn4Z8NTSRyMA2Fd33n5dQ8lWUE00s/"
                crossOrigin="anonymous"
            />
          </Head>
            <Main />
            <NextScript />
        </Html>
      )
    }
