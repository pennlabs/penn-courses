import React from 'react'
import { Link } from 'react-router-dom'
import withLayout from './withLayout'

const About = () => (
  <div className="center-narrow">
    <h1>Hey there!</h1>
    <p>Welcome to the new Penn Course Review!</p>
    <p>
      The student-run Penn Course Review has served as a valuable guide for
      course selection since the 1960s. In 2014, Penn Course Review was
      completely redesigned to simplify the search experience. In 2018, we hope
      to continue providing you with the best insights on courses and have
      therefore updated this experience.
    </p>
    <p>
      Interested in building something on the Penn Course Review API?
      <a href="https://docs.google.com/spreadsheet/viewform?hl=en_US&formkey=dGZOZkJDaVkxdmc5QURUejAteFdBZGc6MQ#gid=0">
        Request API access
      </a>
      .
    </p>
    <p>
      Want easy access to Penn Course Review? Get the{' '}
      <a href="https://pennlabs.org/mobile/">Penn Mobile App</a>!
    </p>

    <h1>About</h1>
    <p>
      Penn Course Review is a student-run service that provides numerical
      ratings for undergraduate courses and professors at the University of
      Pennsylvania. PCR has a long history of being a valuable and influential
      guide for course selection.
    </p>
    <p>
      PCR is developed and managed by
      <a href="https://pennlabs.org/">Penn Labs</a>, a student developer
      organization on Penn’s campus.
    </p>

    <p>
      The Penn Course Review compiles its information from online course
      evaluations conducted at the end of each semester by the Provost's office
      in conjunction with ISC.
    </p>
    <p>
      Your evaluations and comments feed the Review, so the more information you
      provide about your courses and professors, the more comprehensive Penn
      Course Review will be.
    </p>

    <p>
      If you want to look at courses on the go,
      <a href="https://pennlabs.org/mobile/">PennMobile</a> is available for
      download! In the courses section, you are able to view course descriptions
      and ratings!
    </p>
    <p>
      Version 2.0 was built by Eric Wang, Cassandra Li, Rohan Menezes, Vinai
      Rachakonda, Brandon Lin, Yonah Mann, Josh Doman, Jerry Lu, Daniel Tao and
      designed by Tiffany Chang.
    </p>
    <p>Thanks and happy searching,</p>
    <p>
      <strong>Penn Labs</strong>
    </p>

    <img alt="Penn Labs" src="/static/image/labs.png" style={{ width: 100 }} />

    <h1>Questions</h1>
    <p>
      If you have any questions, take a look at our
      <Link to="faq">FAQs</Link> section.
    </p>
  </div>
)

export const AboutPage = withLayout(About)
