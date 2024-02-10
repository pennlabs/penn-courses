import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import React, { useState } from "react";
import { type User } from '../types';
import LoginModal from 'pcx-shared-components/src/accounts/LoginModal';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const updateUser = (newUserVal: User | null) => {
      if (!newUserVal) {
          // the user has logged out; show the login modal
          setShowLoginModal(true);
      } else {
          // the user has logged in; hide the login modal
          setShowLoginModal(false);
      }
      setUser(newUserVal);
  };
  
  return (
    <>  
      <DndProvider backend={HTML5Backend}>
        <Nav
        login={updateUser}
        logout={() => updateUser(null)}
        user={user}
        />
        <FourYearPlanPage />
        {showLoginModal && (
            <LoginModal
                pathname={window.location.pathname}
                siteName="Penn Course Alert"
            />
        )}
      </DndProvider>
    </>
  )
}
