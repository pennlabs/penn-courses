import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import './App.css'

import { Route, Routes } from 'react-router-dom'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import CheckoutPage from './pages/CheckoutPage'
import MainPage from './pages/MainPage'

function App() {

  return (
    <div>
      <Routes>
        <Route
          path='/'
          element={
              <DndProvider backend={HTML5Backend}>
                <MainPage />
              </DndProvider>
          }
        />
      </Routes >
    </div >
  )
}

export default App
