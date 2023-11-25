import { Html, Head, Main, NextScript } from 'next/document'
import React from 'react';

export default function Document() {
  return (
    <Html lang="en" style={{backgroundColor:'#F7F9FC'}}>
      <Head>
        {/* <title>Penn Degree Plan</title> */}
        <meta name="description" content="Penn Degree Plan by Penn Labs" />
      </Head>
        <Main />
        <NextScript />
    </Html>
  )
}
