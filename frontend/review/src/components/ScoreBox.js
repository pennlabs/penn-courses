import React, { Component } from "react";
import { Link } from "react-router-dom";

import {
  capitalize,
  convertInstructorName,
  compareSemesters,
  getColumnName,
  orderColumns,
  convertSemesterToInt,
  toNormalizedSemester
} from "../utils/helpers";
import {
  ColumnSelector,
  CourseDetails,
  PopoverTitle,
  ScoreTable
} from "./common";

import "react-table/react-table.css";

/*
 * Setting this to true colors all other cells depending on its value when compared to the selected row.
 */
const ENABLE_RELATIVE_COLORS = false;

/**
 * The top right box of a review page with the table of numerical scores.
 */
class ScoreBox extends Component {
  constructor(props) {
    super(props);

    this.state = {
      data: null,
      columns: null,
      filtered: [],
      currentInstructors: {},
      currentCourses: {},
      filterAll: "",
      selected: null
    };

    this.updateLiveData = this.updateLiveData.bind(this);
    this.generateColumns = this.generateColumns.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  handleSelect(selected) {
    this.setState({ selected });
    return this.props.onSelect(selected);
  }

  updateLiveData() {
    const instructorTaught = {};
    const { data, liveData, type } = this.props;
    if (type === "course") {
      Object.values(data.instructors).forEach(a => {
        const key = convertInstructorName(a.name);
        instructorTaught[key] = convertSemesterToInt(a.most_recent_semester);
      });

      if (liveData) {
        const instructorsThisSemester = {};
        const { instructors = [], courses } = liveData;
        instructors.forEach(a => {
          const data = {
            open: 0,
            all: 0,
            sections: []
          };
          const key = convertInstructorName(a);
          Object.values(courses).forEach(cat => {
            const coursesByInstructor = cat
              .filter(
                ({ instructors }) =>
                  instructors
                    .map(b => convertInstructorName(b.name))
                    .indexOf(key) !== -1
              )
              .filter(a => !a.is_cancelled);
            data.open += coursesByInstructor.filter(a => !a.is_closed).length;
            data.all += coursesByInstructor.length;
            data.sections = data.sections.concat(
              coursesByInstructor.map(a => a)
            );
          });
          instructorsThisSemester[key] = data;
          instructorTaught[key] = Infinity;
        });
        this.setState(({ data }) => ({
          currentInstructors: instructorTaught,
          data: data.map(a => ({
            ...a,
            star: instructorsThisSemester[convertInstructorName(a.name)]
          }))
        }));
      } else {
        this.setState(({ data }) => ({
          currentInstructors: instructorTaught,
          data: data.map(a => ({ ...a, star: null }))
        }));
      }
    } else if (type === "instructor") {
      if (liveData) {
        const courses = {};
        Object.values(liveData.courses).forEach(a => {
          const key = `${a.course_department}-${a.course_number}`;
          if (!(key in courses)) {
            courses[key] = [];
          }
          courses[key].push(a);
        });
        this.setState({
          currentCourses: courses
        });
      }
    }
  }

  generateColumns() {
    const { data: results, liveData, type } = this.props;

    const columns = {};
    const isCourse = type === "course";
    const isInstructor = type === "instructor";
    const infoMap = isCourse ? results.instructors : results.courses;

    const EXTRA_KEYS = ["latest_semester", "num_semesters"];
    const SEM_SORT_KEY = "latest_semester";

    const data = Object.keys(infoMap).map(key => {
      const val = isCourse ? results.instructors[key] : results.courses[key];
      const output = {};
      Object.keys(val.average_reviews).forEach(col => {
        if (col === "rSemesterCalc" || col === "rSemesterCount") {
          return;
        }
        output[col] = {
          average: val.average_reviews[col]?.toFixed(2),
          recent: val.recent_reviews[col]?.toFixed(2)
        };
        columns[col] = true;
      });
      if (isInstructor) {
        EXTRA_KEYS.forEach(col => {
          if (col === "latest_semester") {
            output[col] = val[col] && toNormalizedSemester(val[col]);
          } else {
            output[col] = val[col];
          }
          columns[col] = true;
        });
      }
      output.key = isCourse ? key : val.code;
      output.name = val.name;
      output.semester = val.most_recent_semester;
      output.code = val.code;
      return output;
    });

    const cols = [];
    if (isInstructor) {
      EXTRA_KEYS.forEach(colName =>
        cols.push({
          id: colName,
          Header: capitalize(colName.replace("_", " ")),
          accessor: colName,
          sortMethod:
            SEM_SORT_KEY === colName
              ? compareSemesters
              : (a, b) => (a > b ? 1 : -1),
          Cell: ({ value }) => {
            const classes = [];
            const val = value || "N/A";

            if (!value) {
              classes.push("empty");
            }

            classes.push(this.props.isAverage ? "cell_average" : "cell_recent");

            return (
              <center>
                <span className={classes.join(" ")}>{val}</span>
              </center>
            );
          },
          width: 140,
          show: true
        })
      );
    }

    orderColumns(Object.keys(columns))
      // Remove columns that don't start with r, as they are not RatingBit values and
      // shouldn't be generated by this logic
      .filter(key => key && key.charAt(0) === "r")
      .forEach(key => {
        const header = getColumnName(key);
        cols.push({
          id: key,
          Header: header,
          accessor: key,
          sortMethod: (a, b) => {
            if (a && b) {
              a = this.props.isAverage ? a.average : a.recent;
              b = this.props.isAverage ? b.average : b.recent;
              return a > b ? 1 : -1;
            }
            return a ? 1 : -1;
          },
          Cell: ({ column: { id }, original: { key }, value = {} }) => {
            const classes = [];
            const { average, recent } = value;
            const val = Object.keys(value).length
              ? this.props.isAverage
                ? average
                : recent
              : "N/A";

            if (!value) {
              classes.push("empty");
            }

            if (this.props.isAverage) {
              classes.push("cell_average");
            } else {
              classes.push("cell_recent");
            }

            if (
              ENABLE_RELATIVE_COLORS &&
              this.state.selected in infoMap &&
              key !== this.state.selected
            ) {
              const other =
                infoMap[this.state.selected][
                  this.props.isAverage ? "average_reviews" : "recent_reviews"
                ][id];
              if (Math.abs(val - other) > 0.01) {
                if (val > other) {
                  classes.push("lower");
                } else {
                  classes.push("higher");
                }
              }
            }

            return (
              <center>
                <span className={classes.join(" ")}>{val}</span>
              </center>
            );
          },
          width: 140,
          show: true
        });
      });

    cols.unshift({
      id: "name",
      Header: isCourse ? "Instructor" : "Course",
      accessor: "name",
      width: 270,
      show: true,
      required: true,
      Cell: ({ original: { code, key, star }, value }) => (
        <span>
          {isCourse && (
            <Link
              to={`/instructor/${key}`}
              title={`Go to ${value}`}
              className="mr-1"
              style={{ color: "rgb(102, 146, 161)" }}
            >
              <i className="instructor-link far fa-user" />
            </Link>
          )}
          {value}
          {star && liveData && (
            <PopoverTitle
              title={
                <span>
                  <b>{value}</b> is teaching during <b>{liveData.term}</b> and{" "}
                  <b>{star.open}</b> out of <b>{star.all}</b>{" "}
                  {star.all === 1 ? "section" : "sections"}{" "}
                  {star.open === 1 ? "is" : "are"} open.
                  <ul>
                    {star.sections
                      .sort((x, y) =>
                        x.section_id_normalized.localeCompare(
                          y.section_id_normalized
                        )
                      )
                      .map(data => (
                        <CourseDetails
                          key={data.section_id_normalized}
                          data={data}
                        />
                      ))}
                  </ul>
                </span>
              }
            >
              <i className={`fa-star ml-1 ${star.open ? "fa" : "far"}`} />
            </PopoverTitle>
          )}
          {isInstructor && Boolean(this.state.currentCourses[code]) && (
            <PopoverTitle
              title={
                <span>
                  <b>{results.name}</b> will teach{" "}
                  <b>{code.replace("-", " ")}</b> in{" "}
                  <b>{this.state.currentCourses[code][0].term_normalized}</b>.
                  <ul>
                    {this.state.currentCourses[code].map(data => (
                      <CourseDetails
                        key={data.section_id_normalized}
                        data={data}
                      />
                    ))}
                  </ul>
                </span>
              }
            >
              <i
                className={`ml-1 fa-star ${
                  this.state.currentCourses[code].filter(
                    a => !a.is_closed && !a.is_cancelled
                  ).length
                    ? "fa"
                    : "far"
                }`}
              />
            </PopoverTitle>
          )}
        </span>
      ),
      sortMethod: (a, b) => {
        const aname = convertInstructorName(a);
        const bname = convertInstructorName(b);
        const hasStarA = this.state.currentInstructors[aname];
        const hasStarB = this.state.currentInstructors[bname];
        if (hasStarA && !hasStarB) {
          return -1;
        }
        if (!hasStarA && hasStarB) {
          return 1;
        }
        if (hasStarA !== hasStarB) {
          return hasStarB - hasStarA;
        }
        return a.localeCompare(b);
      },
      filterMethod: (filter, rows) => {
        if (filter.value === "") {
          return true;
        }
        return rows[filter.id]
          .toLowerCase()
          .includes(filter.value.toLowerCase());
      }
    });
    if (!isCourse) {
      cols.unshift({
        id: "code",
        Header: "Code",
        accessor: "code",
        width: 100,
        show: true,
        required: true,
        Cell: ({ value }) => (
          <center>
            <Link to={`/course/${value}`} title={`Go to ${value}`}>
              {value}
            </Link>
          </center>
        )
      });
    }
    this.setState({ data, columns: cols });

    if (liveData) {
      this.updateLiveData();
    }
  }

  componentDidUpdate(prevProps) {
    const { data, liveData } = this.props;
    if (prevProps.data !== data || prevProps.liveData !== liveData) {
      this.generateColumns();
    }
  }

  componentDidMount() {
    this.generateColumns();
  }

  render() {
    const { data, columns, filterAll, filtered } = this.state;
    const { type, isAverage, setIsAverage } = this.props;
    const isCourse = type === "course";

    if (!data) {
      return <h1>Loading Data...</h1>;
    }

    return (
      <div className="box">
        <div className="clearfix">
          <div className="btn-group">
            <button
              onClick={() => setIsAverage(true)}
              className={`btn btn-sm ${
                this.props.isAverage ? "btn-primary" : "btn-secondary"
              }`}
            >
              Average
            </button>
            <button
              onClick={() => setIsAverage(false)}
              className={`btn btn-sm ${
                this.props.isAverage ? "btn-secondary" : "btn-primary"
              }`}
            >
              Most Recent
            </button>
          </div>
          <ColumnSelector
            name="score"
            type={type}
            columns={columns}
            onSelect={columns => this.setState({ columns })}
          />
          <div className="float-right">
            <label className="table-search">
              <input
                value={filterAll}
                onChange={val =>
                  this.setState({
                    filtered: [{ id: "name", value: val.target.value }],
                    filterAll: val.target.value
                  })
                }
                type="search"
                className="form-control form-control-sm"
              />
            </label>
          </div>
        </div>
        <ScoreTable
          multi={type === "department"}
          sorted={[{ id: isCourse ? "name" : "code", desc: false }]}
          filtered={filtered}
          data={data}
          columns={columns}
          onSelect={this.handleSelect}
          noun={isCourse ? "instructor" : "course"}
          isAverage={isAverage}
        />
      </div>
    );
  }
}

export default ScoreBox;
