import Head from 'next/head'
import Image from 'next/image'
import { Inter } from 'next/font/google'
import styles from '@/styles/Home.module.css'

import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import MainPage from './MainPage'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  return (
    <>  
      <Head>
        <title>Create Next App</title>
        <meta name="description" content="Penn Degree Plan by Penn Labs" />
      </Head>
      {/* <main className={styles.main}> */}
              <DndProvider backend={HTML5Backend}>
                <MainPage />
              </DndProvider>
      {/* </main> */}
    </>
  )
}
