import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import SearchBar from './SearchBar'

/**
 * The navigation bar at the top of the page, containing the logo, search bar, and cart icon.
 */

const Navbar = () => {
  const getCourseCount = () =>
    Object.keys(localStorage).filter(a => !a.startsWith('meta-')).length
  const [courseCount, setCourseCount] = useState(getCourseCount())

  useEffect(() => {
    const onStorageChange = () => setCourseCount(getCourseCount())
    window.addEventListener('storage', onStorageChange)
    window.onCartUpdated = onStorageChange
    return () => {
      window.removeEventListener('storage', onStorageChange)
      window.onCartUpdated = null
    }
  }, [])

  return (
    <div id="header">
      <span className="float-left">
        <Link to="/" title="Go to Penn Course Review Home">
          <div id="logo" />
        </Link>
        <SearchBar />
      </span>
      <span className="float-right">
        <Link to="/cart" id="cart-icon" title="Course Cart">
          <i id="cart" className="fa fa-shopping-cart" />
          {courseCount > 0 && <span id="cart-count">{courseCount}</span>}
        </Link>
      </span>
    </div>
  )
}

export default Navbar
