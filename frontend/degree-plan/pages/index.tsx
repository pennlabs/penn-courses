import { Inter } from 'next/font/google'

import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import MainPage from './MainPage'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  return (
    <>  
        <DndProvider backend={HTML5Backend}>
          <MainPage />
        </DndProvider>
    </>
  )
}
