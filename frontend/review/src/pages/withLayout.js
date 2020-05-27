import React from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default WrappedComponent => props => (
  <>
    <Navbar />
    <WrappedComponent {...props} />
    <Footer />
  </>
)
