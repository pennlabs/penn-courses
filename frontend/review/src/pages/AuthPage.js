import React, { useEffect, useState } from 'react'
import Cookies from 'js-cookie'

import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { ReviewPage } from './ReviewPage'
import { ErrorBox } from '../components/common'
import { redirectForAuth, apiIsAuthenticated } from '../utils/api'

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */

export const AuthPage = props => {
  const [authed, setAuthed] = useState(true)
  const [authFailed, setAuthFailed] = useState(false)

  // useEffect(() => {
  //   const tempCookie = 'doing_token_auth'
  //   apiIsAuthenticated(authed => {
  //     if (authed) {
  //       Cookies.remove(tempCookie)
  //       setAuthed(true)
  //       setAuthFailed(false)
  //     } else {
  //       const timestamp = new Date().getTime().toString()
  //       if (typeof Cookies.get(tempCookie) === 'undefined') {
  //         Cookies.set(tempCookie, timestamp, { expires: 1 / 1440 })
  //         redirectForAuth()
  //         setAuthed(false)
  //         setAuthFailed(false)
  //       } else {
  //         const oldTimestamp = Cookies.get(tempCookie)
  //         Cookies.remove(tempCookie)
  //         setAuthed(false)
  //         setAuthFailed(true)
  //         window.Raven.captureMessage(
  //           `Could not perform Platform authentication: status ${authed} old ${oldTimestamp} current ${timestamp}`,
  //           { level: 'error' }
  //         )
  //       }
  //     }
  //   })
  // }, [])

  if (authFailed) {
    return (
      <>
        <Navbar />
        <ErrorBox>
          Could not perform Platform authentication.
          <br />
          Refresh this page to try again.
        </ErrorBox>
        <Footer />
      </>
    )
  }
  // TODO: Add loading spinner instead of null
  return authed ? <ReviewPage {...props} /> : null
}
