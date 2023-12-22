import React, { Component } from "react";
import Cookies from "universal-cookie";
import InfoBox from "../components/InfoBox";
import ScoreBox from "../components/ScoreBox";
import GraphBox from "../components/GraphBox";
import Navbar from "../components/Navbar";
import DetailsBox from "../components/DetailsBox";
import SearchBar from "../components/SearchBar";
import Footer from "../components/Footer";
import { ErrorBox } from "../components/common";
import { apiReviewData, apiLive } from "../utils/api";

/**
 * Represents a course, instructor, or department review page.
 */
export class ReviewPage extends Component {
  constructor(props) {
    super(props);
    this.tableRef = React.createRef();
    this.cookies = new Cookies();
    this.state = {
      type: this.props.match.params.type,
      code: this.props.match.params.code,
      url_code: this.props.match.params.code,
      url_semester: this.props.match.params.semester,
      data: null,
      error: null,
      error_detail: null,
      rowCode: null,
      liveData: null,
      selectedCourses: {},
      isAverage: localStorage.getItem("meta-column-type") !== "recent",
      isCourseEval: false,
      showBanner: false
    };

    this.navigateToPage = this.navigateToPage.bind(this);
    this.getReviewData = this.getReviewData.bind(this);
    this.setIsAverage = this.setIsAverage.bind(this);
    const setIsCourseEval = this.setIsCourseEval.bind(this);
    this.setIsCourseEval = val => {
      setIsCourseEval(val);
      window.ga("send", "event", {
        eventCategory: "Registration Metrics Mode",
        eventAction: "Toggle",
        eventValue: val
      });
    };
    this.showRowHistory = this.showRowHistory.bind(this);
    this.showDepartmentGraph = this.showDepartmentGraph.bind(this);
  }

  componentDidMount() {
    this.getReviewData();

    fetch("https://platform.pennlabs.org/options/")
      .then(response => response.json())
      .then(options =>
        this.setState({
          showBanner: options.RECRUITING && !this.cookies.get("hide_pcr_banner")
        })
      );
  }

  componentDidUpdate(prevProps) {
    if (
      this.props.match.params.type !== prevProps.match.params.type ||
      this.props.match.params.code !== prevProps.match.params.code ||
      this.props.match.params.semester !== prevProps.match.params.semester
    ) {
      // TODO: Switch to functional component and use useEffect(() => {...}, [])
      // eslint-disable-next-line react/no-did-update-set-state
      this.setState(
        {
          type: this.props.match.params.type,
          code: this.props.match.params.code,
          url_code: this.props.match.params.code,
          url_semester: this.props.match.params.semester,
          data: null,
          liveData: null,
          rowCode: null,
          error: null,
          isCourseEval: false
        },
        this.getReviewData
      );
    }
  }

  setIsAverage(isAverage) {
    this.setState({ isAverage }, () =>
      localStorage.setItem("meta-column-type", isAverage ? "average" : "recent")
    );
  }

  //add to local storage?
  setIsCourseEval(isCourseEval) {
    this.setState({ isCourseEval });
  }

  getPageInfo() {
    const pageInfo = window.location.pathname.substring(1).split("/");

    if (["course", "instructor", "department"].indexOf(pageInfo[0]) === -1) {
      pageInfo[0] = null;
      pageInfo[1] = null;
    }

    return pageInfo;
  }

  getReviewData() {
    const { type, code, url_code, url_semester } = this.state;
    if (type && code) {
      apiReviewData(type, code, url_semester)
        .then(data => {
          const { error, detail } = data;
          if (error) {
            this.setState({
              error,
              error_detail: detail
            });
          } else {
            this.setState({ data });
            if (type === "course") {
              apiLive(data.code, url_semester && `${url_code}@${url_semester}`)
                .then(result => this.setState({ liveData: result }))
                .catch(() => undefined);
            }
          }
        })
        .catch(() =>
          this.setState({
            error:
              "Could not retrieve review information at this time. Please try again later!"
          })
        );
    }
  }

  navigateToPage(value) {
    if (!value) {
      return;
    }
    this.props.history.push(value);
  }

  showRowHistory(nextCode) {
    const { rowCode } = this.state;
    if (nextCode === rowCode) {
      this.setState({ rowCode: null });
      return;
    }
    this.setState({ rowCode: nextCode }, () => {
      if (nextCode) {
        window.scrollTo({
          behavior: "smooth",
          top: this.tableRef.current.offsetTop
        });
      }
    });
  }

  showDepartmentGraph(selectedCourses) {
    this.setState({ selectedCourses });
  }

  static getDerivedStateFromError() {
    return { error: "An unknown error occurred." };
  }

  render() {
    if (this.state.error) {
      return (
        <div>
          <Navbar />
          <ErrorBox detail={this.state.error_detail}>
            {this.state.error}
          </ErrorBox>
          <Footer />
        </div>
      );
    }

    if (!this.state.code) {
      return (
        <div id="content" className="row">
          {this.state.showBanner && (
            <div id="banner">
              <span role="img" aria-label="Party Popper Emoji">
                🎉
              </span>{" "}
              <b>Want to build impactful products like Penn Course Review?</b>{" "}
              Join Penn Labs this spring! Apply{" "}
              <a
                href="https://pennlabs.org/apply"
                target="_blank"
                rel="noopener noreferrer"
              >
                here
              </a>
              !{" "}
              <span role="img" aria-label="Party Popper Emoji">
                🎉
              </span>
              <span
                className="close"
                onClick={e => {
                  this.setState({ showBanner: false });
                  this.cookies.set("hide_pcr_banner", true, {
                    expires: new Date(Date.now() + 12096e5)
                  });
                  e.preventDefault();
                }}
              >
                <i className="fa fa-times" />
              </span>
            </div>
          )}
          <div className="col-md-12">
            <div id="title">
              <img src="/static/image/logo.png" alt="Penn Course Review" />{" "}
              <span className="title-text">Penn Course Review</span>
            </div>
          </div>
          <SearchBar isTitle />
          <Footer style={{ marginTop: 150 }} />
        </div>
      );
    }

    const {
      code,
      url_semester,
      data,
      rowCode,
      liveData,
      isAverage,
      isCourseEval,
      selectedCourses,
      type
    } = this.state;

    const handleSelect = {
      instructor: this.showRowHistory,
      course: this.showRowHistory,
      department: this.showDepartmentGraph
    }[type];

    return (
      <div>
        <Navbar />
        {this.state.data ? (
          <>
            <div id="content" className="row">
              <div className="col-sm-12 col-md-4 sidebar-col box-wrapper">
                <InfoBox
                  type={type}
                  code={code}
                  url_semester={url_semester}
                  data={data}
                  liveData={liveData}
                  selectedCourses={selectedCourses}
                  isCourseEval={isCourseEval}
                  setIsCourseEval={this.setIsCourseEval}
                />
              </div>
              <div className="col-sm-12 col-md-8 main-col">
                <ScoreBox
                  data={data}
                  type={type}
                  liveData={liveData}
                  onSelect={handleSelect}
                  isAverage={isAverage}
                  setIsAverage={this.setIsAverage}
                  isCourseEval={isCourseEval}
                />
                {type === "course" && (
                  <DetailsBox
                    type={type}
                    course={code}
                    url_semester={url_semester}
                    instructor={rowCode}
                    isCourseEval={isCourseEval}
                    ref={this.tableRef}
                  />
                )}

                {type === "instructor" && (
                  <DetailsBox
                    type={type}
                    course={rowCode}
                    instructor={code}
                    isCourseEval={isCourseEval}
                    ref={this.tableRef}
                  />
                )}
              </div>
            </div>
            {type === "course" && isCourseEval && (
              <GraphBox
                key={isAverage}
                courseCode={code}
                url_semester={url_semester}
                isAverage={isAverage}
                setIsAverage={this.setIsAverage}
              />
            )}
          </>
        ) : (
          <div style={{ textAlign: "center", padding: 45 }}>
            <i
              className="fa fa-spin fa-cog fa-fw"
              style={{ fontSize: "150px", color: "#aaa" }}
            />
            <h1 style={{ fontSize: "2em", marginTop: 15 }}>
              Loading {type === "instructor" ? "" : code}...
            </h1>
          </div>
        )}
        <Footer />
      </div>
    );
  }
}
