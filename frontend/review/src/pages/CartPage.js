import React, { Component } from 'react'
import { Link } from 'react-router-dom'

import withLayout from './withLayout'
import { Popover } from '../components/common'
import { getColumnName, getCartCourses } from '../utils/helpers'

import {
  DEFAULT_COLUMNS,
  ALL_DATA_COLUMNS,
  COLUMN_FULLNAMES,
  COLUMN_SHORTNAMES,
} from '../constants'

class Cart extends Component {
  constructor(props) {
    super(props)

    this.state = {
      showChooseCols: false,
      isAverage: localStorage.getItem('meta-column-type') !== 'recent',
      courses: [],
      excludedCourses: [],
      boxValues: ['N/A', 'N/A', 'N/A', 'N/A'],
      boxLabels: DEFAULT_COLUMNS,
    }

    // TODO: Move regeneration logic into Redux or React Context
    this.regenerateRatings = this.regenerateRatings.bind(this)
  }

  componentDidMount() {
    window.addEventListener('storage', this.regenerateRatings)
    this.regenerateRatings()
  }

  componentWillUnmount() {
    window.removeEventListener('storage', this.regenerateRatings)
  }

  regenerateRatings() {
    const courses = getCartCourses()
    this.setState(({ boxLabels, excludedCourses, isAverage }) => ({
      courses,
      boxValues: boxLabels.map(type => {
        const scoreList = courses
          .filter(
            a =>
              typeof a !== 'undefined' &&
              excludedCourses.indexOf(a.course) === -1
          )
          .map(
            a =>
              ((a.info || { type: null })[type] || {
                average: null,
                recent: null,
              })[isAverage ? 'average' : 'recent']
          )
          .filter(a => a !== null && !isNaN(a))
          .map(a => parseFloat(a))
        return scoreList.length
          ? (scoreList.reduce((a, b) => a + b) / scoreList.length).toFixed(1)
          : 'N/A'
      }),
    }))

    if (window.onCartUpdated) window.onCartUpdated()
  }

  render() {
    const {
      boxLabels,
      boxValues,
      courses,
      excludedCourses,
      showChooseCols,
      isAverage,
    } = this.state

    return (
      <center className="box" style={{ margin: '30px auto', maxWidth: 720 }}>
        <p className="courseCartHeader title">My Course Cart</p>
        <p className="courseCartDesc">
          The course cart is a feature for you to see all the relevant reviews
          for your selected courses at once with at-a-glance statistics. Search
          for courses to add them to your cart.
        </p>
        <div id="bannerScore">
          <div className="scoreboxrow courseCartRow">
            {boxLabels.map((a, i) => (
              <div
                key={a}
                className={`mb-2 scorebox ${
                  ['course', 'instructor', 'difficulty', 'workload'][i % 4]
                }`}
              >
                <p className="num">{boxValues[i]}</p>
                <p className="desc">{COLUMN_SHORTNAMES[a]}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="clear" />
        <div className="fillerBox" />
        {showChooseCols && (
          <div className="box">
            <h3 style={{ fontSize: '1.5em' }}>Choose columns to display</h3>
            <div className="clearfix" style={{ textAlign: 'left' }}>
              {ALL_DATA_COLUMNS.map(a => (
                <div style={{ width: '50%', display: 'inline-block' }} key={a}>
                  <input
                    type="checkbox"
                    onChange={() => {
                      const pos = boxLabels.indexOf(a)
                      if (pos === -1) {
                        this.setState(state => {
                          state.boxValues.push('N/A')
                          state.boxLabels.push(a)
                          return {
                            boxValues: state.boxValues,
                            boxLabels: state.boxLabels,
                          }
                        })
                      } else {
                        this.setState(state => {
                          state.boxValues.splice(pos, 1)
                          state.boxLabels.splice(pos, 1)
                          return {
                            boxValues: state.boxValues,
                            boxLabels: state.boxLabels,
                          }
                        })
                      }
                      this.regenerateRatings()
                    }}
                    checked={boxLabels.indexOf(a) !== -1}
                    value={a}
                    id={`checkbox_${a}`}
                    name={a}
                    className="mr-1"
                  />
                  <label htmlFor={`checkbox_${a}`}>{COLUMN_FULLNAMES[a]}</label>
                </div>
              ))}
            </div>
          </div>
        )}
        <button
          className="btn btn-primary mr-2"
          onClick={() =>
            this.setState(state => ({
              showChooseCols: !state.showChooseCols,
            }))
          }
        >
          Choose Categories
        </button>
        <div className="btn-group">
          <span
            className={`btn ${isAverage ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              this.setState({ isAverage: true }, () =>
                localStorage.setItem('meta-column-type', 'average')
              )
              this.regenerateRatings()
            }}
          >
            Average
          </span>
          <span
            className={`btn ${isAverage ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => {
              this.setState({ isAverage: false }, () =>
                localStorage.setItem('meta-column-type', 'recent')
              )
              this.regenerateRatings()
            }}
          >
            Most Recent
          </span>
        </div>
        <div className="clear" />
        <div id="boxHelpTag">
          Click a course to exclude it from the average.
        </div>
        <div id="courseBox">
          {courses.map(({ course, instructor, info }, i) => (
            <Popover
              key={i}
              button={
                <div
                  onClick={() => {
                    this.setState({
                      excludedCourses:
                        excludedCourses.indexOf(course) !== -1
                          ? excludedCourses.filter(b => b !== course)
                          : excludedCourses.concat([course]),
                    })
                    this.regenerateRatings()
                  }}
                  style={{ display: 'inline-block' }}
                  className={`courseInBox${
                    excludedCourses.indexOf(course) !== -1
                      ? ' courseInBoxGrayed'
                      : ''
                  }`}
                >
                  {course}
                  <Link to={`/course/${course}`}>
                    <i className="fa fa-link" />
                  </Link>
                  <i
                    className="fa fa-times"
                    onClick={() => {
                      localStorage.removeItem(course)
                      this.regenerateRatings()
                    }}
                  />
                </div>
              }
              hover
            >
              <b>{course}</b>
              <br />
              {instructor}
              <br />
              {info &&
                Object.values(info)
                  .sort((x, y) => x.category.localeCompare(y.category))
                  .map(({ category, average, recent }, i) => (
                    <div key={i}>
                      {getColumnName(category)}{' '}
                      <span className="float-right ml-3">
                        {isAverage ? average : recent}
                      </span>
                    </div>
                  ))}
            </Popover>
          ))}
        </div>
      </center>
    )
  }
}

export const CartPage = withLayout(Cart)
