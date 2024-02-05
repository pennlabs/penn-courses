import Head from 'next/document'
import Image from 'next/image'
import { Inter } from 'next/font/google'
import styles from '@/styles/Home.module.css'

import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import MainPage from './MainPage'
import CreateDegreePlanModal from '@/components/CreateDegreePlanModal'
import { useEffect, useState } from 'react'
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import Nav from '@/components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage'
import { DegreePlan, User } from '@/types'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showCreateDegreePlanModal, setShowCreateDegreePlanModal] = useState(false)
  const [forceDegreePlanModal, setForceDegreePlanModal] = useState(false)
  const [currentDegreePlan, setCurrentDegreePlan] = useState<DegreePlan | null>(null)
  const [degreePlans, setDegreePlans] = useState<DegreePlan[]>([])
  const [user, setUser] = useState<User | null>(null)

  // authentication
  useEffect(() => {
    fetch("/accounts/me/")
      .then((res) => {
        if (res.status === 403) {
          setShowLoginModal(true)
          console.log("SHOW LOGIN MODAL");
        } else if (!res.ok) {
          console.error(res)
        }
        return res.json()
      })
      .then((res) => {
        if (res) {
          setUser(res)
        }
      })
      .catch((err) => {
        console.error(err)
      })
  }, [])

  // try to fetch degree plans
  useEffect(() => {
    if (currentDegreePlan) return;
    fetch("/api/degree/degreeplans")
      .then((res) => {
        if (!res.ok) {
          console.error(res)
        }
        return res.json()
      })
      .then((res) => {
        if (res.length > 0) {
          setDegreePlans(res)
          setCurrentDegreePlan(res[0])
        } else {
          setShowCreateDegreePlanModal(true)
          setForceDegreePlanModal(true)
        }
      })
      .catch((err) => {
        console.error(err)
      })
  }, [])

  // add a new degree plan
  const addDegreePlan = (degreePlan: DegreePlan) => {
    setCurrentDegreePlan(degreePlan);
    setDegreePlans([...degreePlans, degreePlan]);
  }

  return (
    <>  
        {showLoginModal && (
            <LoginModal
                pathname={window.location.href}
                siteName="Penn Degree Plan"
            />
        )}
        <CreateDegreePlanModal 
        open={showCreateDegreePlanModal} 
        setOpen={setShowCreateDegreePlanModal} 
        addDegreePlan={addDegreePlan} 
        force={forceDegreePlanModal}
        />
        <DndProvider backend={HTML5Backend}>
            <Nav user={user} />
            <FourYearPlanPage />
        </DndProvider>
    </>
  )
}
