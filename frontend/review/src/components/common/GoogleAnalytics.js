import { useEffect } from 'react'
import { useHistory, useLocation } from 'react-router-dom'

/**
 * Dummy component to make Google Analytics work well with React router.
 */

export const GoogleAnalytics = () => {
  const { action } = useHistory()
  const location = useLocation()
  useEffect(() => {
    if (action === 'PUSH') {
      const { pathname, search } = location
      window.ga('set', 'page', pathname + search)
      window.ga('send', 'pageview')
    }
  }, [location, action])
  return null
}
