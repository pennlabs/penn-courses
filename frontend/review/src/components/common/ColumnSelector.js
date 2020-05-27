import React, { Component } from 'react'

import { DEFAULT_COLUMNS } from '../../constants'
import { Popover } from './Popover'

/**
 * Used to select the columns that appear in a table.
 */
export class ColumnSelector extends Component {
  constructor(props) {
    super(props)
    const { columns, type, name } = props
    let defaultColumns = localStorage.getItem(`meta-${name}`)
    if (defaultColumns) {
      defaultColumns = JSON.parse(defaultColumns)
    } else {
      const instructorFields =
        type === 'instructor'
          ? {
              latest_semester: true,
              num_semesters: true,
            }
          : {}

      const defaultFields = {}
      DEFAULT_COLUMNS.forEach(col => {
        defaultFields[col] = true
      })

      defaultColumns = {
        ...instructorFields,
        ...defaultFields,
      }
    }
    this.defaultColumns = defaultColumns

    this.handleToggleGenerator = this.handleToggleGenerator.bind(this)
    this.setAllColumns = this.setAllColumns.bind(this)
    this.changeColumns = this.changeColumns.bind(this)

    this.changeColumns(
      columns.map(a => ({ ...a, show: a.required || !!defaultColumns[a.id] }))
    )
  }

  changeColumns(cols) {
    const newColumns = cols.reduce((map, obj) => {
      map[obj.id] = obj.show
      return map
    }, {})
    const { name, onSelect } = this.props
    this.defaultColumns = Object.assign(this.defaultColumns, newColumns)
    localStorage.setItem(`meta-${name}`, JSON.stringify(this.defaultColumns))
    onSelect(cols)
  }

  handleToggleGenerator(i) {
    return () => {
      const columnsCopy = Array.from(this.props.columns)
      columnsCopy[i] = { ...columnsCopy[i], show: !columnsCopy[i].show }
      this.changeColumns(columnsCopy)
    }
  }

  setAllColumns(val) {
    return () => {
      const columnsCopy = this.props.columns.map(a => ({
        ...a,
        show: a.required || val,
      }))
      this.changeColumns(columnsCopy)
    }
  }

  render() {
    let x = 0
    const { buttonStyle = 'btn', columns } = this.props
    const button = (
      <button
        aria-label="Choose Columns"
        className={`btn btn-sm ml-2 ${buttonStyle}-secondary`}
      >
        Edit Columns
        <img
          alt="Edit Icon"
          className="btn-image ml-2"
          src={`/static/image/selectcol-${buttonStyle}.svg`}
        />
      </button>
    )

    return (
      <Popover style={{ width: 340 }} button={button}>
        <span
          onClick={this.setAllColumns(true)}
          className={`btn mb-2 mr-2 btn-sm ${buttonStyle}-secondary`}
          style={{ width: 150, textAlign: 'center' }}
        >
          Select all
        </span>
        <span
          onClick={this.setAllColumns(false)}
          className={`btn mb-2 btn-sm ${buttonStyle}-secondary`}
          style={{ width: 150, textAlign: 'center' }}
        >
          Clear
        </span>
        <hr />
        {columns.map(({ required, show, Header: header }, i) => {
          if (required) return false
          x += 1
          const marginClass = x % 2 === 1 ? 'mr-2' : ''
          const buttonClass = `${buttonStyle}${
            show ? '-primary' : '-secondary'
          }`
          return (
            <span
              key={i}
              onClick={this.handleToggleGenerator(i)}
              style={{ width: 150, textAlign: 'center' }}
              className={`btn mt-2 btn-sm ${marginClass} ${buttonClass}`}
            >
              {header}
            </span>
          )
        })}
      </Popover>
    )
  }
}
