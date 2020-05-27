import React from 'react'
import { Link } from 'react-router-dom'
import { getLogoutUrl } from '../utils/api'

/**
 * The footer of every page.
 */
const Footer = ({ style }) => (
  <div style={style} id="footer">
    <div id="footer-inner">
      <Link to="/about">About</Link> | <Link to="/faq">FAQs</Link> |{' '}
      <a
        target="_blank"
        rel="noopener noreferrer"
        href="https://airtable.com/shrVygSaHDL6BswfT"
      >
        Feedback
      </a>{' '}
      | <a href={getLogoutUrl()}>Logout</a>
      <p id="copyright">
        Made with <i style={{ color: '#F56F71' }} className="fa fa-heart" /> by{' '}
        <a href="https://pennlabs.org">
          <strong>Penn Labs</strong>
        </a>{' '}
        | Hosted by{' '}
        <a href="https://stwing.upenn.edu/">
          <strong>STWing</strong>
        </a>
      </p>
    </div>
  </div>
)

export default Footer
