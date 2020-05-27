import React from 'react'
import { Bar } from 'react-chartjs-2'

import { DEFAULT_COLUMNS } from '../../constants'
import { getColumnName } from '../../utils/helpers'

export const DepartmentHeader = ({ name, code }) => (
  <div className="department">
    <div className="title">{name}</div>
    <p className="subtitle">{code}</p>
  </div>
)

const chartColorMap = {
  rCourseQuality: '#6274f1',
  rInstructorQuality: '#ffc107',
  rDifficulty: '#76bf96',
  rWorkRequired: '#df5d56',
}

const generateChartData = courses => {
  return {
    labels: Object.values(courses).map(({ original: { code } }) => code),
    datasets: DEFAULT_COLUMNS.map(column => ({
      label: getColumnName(column),
      data: Object.values(courses).map(
        ({
          original: {
            [column]: { average = 0 },
          },
        }) => average
      ),
      backgroundColor: chartColorMap[column],
    })),
  }
}

const chartOptions = {
  scales: {
    yAxes: [
      {
        display: true,
        ticks: {
          min: 0,
          max: 4,
        },
      },
    ],
  },
}

export const DepartmentGraphs = ({ courses }) => {
  const chartData =
    courses && Object.keys(courses).length && generateChartData(courses)
  return (
    <div className="department-content">
      {chartData ? (
        <div id="row-select-chart-container">
          <Bar data={chartData} options={chartOptions} />
        </div>
      ) : (
        <div id="row-select-placeholder">
          <object type="image/svg+xml" data="/static/image/selectrow.svg">
            <img alt="Select Row" src="/static/image/selectrow.svg" />
          </object>
          <div id="row-select-text">
            Select a few rows to begin comparing courses.
          </div>
        </div>
      )}
    </div>
  )
}
