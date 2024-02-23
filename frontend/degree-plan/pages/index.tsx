import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import React, { useState } from "react";
import { type User } from '../types';
import LoginModal from 'pcx-shared-components/src/accounts/LoginModal';
import { SWRConfig } from 'swr';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [searchClosed, setSearchClosed] = useState(true);
  const [reqId, setReqId] = useState<undefined | number>(undefined);

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
        <SWRConfig value={{
          fetcher: (resource, init) => fetch(resource, init).then(res => res.json()),
          onError: (error, key) => {
            if (error.status !== 403 && error.status !== 404) {
              // error handling
            }
          }
        }}>
          <Nav
            login={updateUser}
            logout={() => updateUser(null)}
            user={user}
            setSearchClosed={setSearchClosed}
            setReqId={setReqId}
          />
          <FourYearPlanPage searchClosed={searchClosed} setSearchClosed={setSearchClosed} reqId={reqId} setReqId={setReqId}/>
          {showLoginModal && (
              <LoginModal
                  pathname={window.location.pathname}
                  siteName="Penn Degree Plan"
              />
          )}
        </SWRConfig>
      </DndProvider>
    </>
  )
}
