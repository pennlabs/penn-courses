import React from 'react'
import withLayout from './withLayout'

const FAQ = () => (
  <div id="faqs" className="center-narrow">
    <h1>Frequently Asked Questions</h1>
    <div>
      <p className="question">How do I use the website?</p>
      <p className="answer">
        Each professor, course, and department has its own page. Summary ratings
        for the recent semester and for all semesters are provided at the left
        of each page, with more detailed rating information provided on the
        right. You can choose to view or hide each course rating criteria by
        clicking the plus icon on the top of the table. You can also toggle the
        view mode of ratings between aggregate and most recent on the right side
        of the page. You can hover over the tags on the left side of the page or
        the stars on the right side of the page in order to learn more about
        courses offered in the upcoming semester.
      </p>
    </div>

    <div>
      <p className="question">What's new?</p>
      <p className="answer">
        The site includes new features intended to make PCR's content more
        intuitive and accessible. The new search function allows students to
        search by course name, number, or professor. In addition to the
        traditional ratings, the site now offers ratings that average the
        evaluations from every semester the course or professor has been
        reviewed. Students can choose which information is relevant to them by
        selecting which rating criteria appear on the page.
      </p>
    </div>

    <div>
      <p className="question">How are courses rated?</p>
      <p className="answer">
        At the end of each semester, the Provost's office, in conjunction with
        ISC, administers Penn's course evaluation form, which consists of eleven
        questions aimed at assessing the quality of the course and instructor.
        Each evaluation question is answered on a scale of Poor to Excellent.
        The ratings are translated numerically so that a rating of 0.00
        corresponds a student evaluation of "Poor," 1.00 corresponds to an
        evaluation of "Fair," 2.00 to "Good," 3.00 to "Very Good," and 4.00 to
        "Excellent."
      </p>
    </div>

    <div>
      <p className="question">How often is data updated?</p>
      <p className="answer">
        Information pertaining to which sections are taught in the upcoming
        semester is updated every 24 hours.
      </p>
    </div>

    <div>
      <p className="question">What do the colors mean?</p>
      <div className="answer">
        Here's a guide to the color coded ratings.
        <br />
        <br />
        <div className="scorebox difficulty rating-bad">
          <div className="num">0-2</div>
        </div>
        <div className="scorebox difficulty rating-okay">
          <div className="num">2-3</div>
        </div>
        <div className="scorebox difficulty rating-good">
          <div className="num">3-4</div>
        </div>
      </div>
    </div>
  </div>
)

export const FAQPage = withLayout(FAQ)
