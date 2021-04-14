import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { Bar } from "react-chartjs-2";

const LoadingContainer = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const ChartTitle = styled.div`
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
`;

const ChartDescription = styled.div`
  font-size: 12px;
  font-weight: normal;
  color: #b2b2b2;
  margin-bottom: 10px;
`;

const sumOfSubArray = (start, end, data) => {
  let sum = 0;
  for (let i = start; i <= end; i++) {
    sum += data[i][1];
  }
  return sum;
};

const generateChartData = (data, isPercent) => {
  return {
    labels: data.map((point) =>
      Math.round(point[0] * 100) % 10 === 0 ? (point[0] * 100).toFixed() : ""
    ),
    datasets: [
      {
        type: "line",
        label: "5% Period Average",
        data: data.map((point, index) => {
          // console.log(point[1]);
          let average;
          if (index - 5 < 0) {
            average = sumOfSubArray(0, index, data) / index;
          } else {
            average = sumOfSubArray(index - 5, index, data) / 5;
          }
          return Math.round(average * 100) / (isPercent ? 1 : 100);
        }),
        borderColor: "#6378E9",
        borderWidth: 3,
        fill: false,
      },
      {
        type: "bar",
        label: "Demand",
        data: data.map(
          (point) => Math.round(point[1] * 100) / (isPercent ? 1 : 100)
        ),
        backgroundColor: "#AAACEC",
      },
    ],
  };
};

const chartOptions = {
  elements: {
    point: {
      radius: 0,
    },
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start",
  },
  scales: {
    autoSkip: true,
    xAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          beginAtZero: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
          max: 100,
          stepSize: 10,
          callback: function(value) {
            return value + "%";
          },
        },

        scaleLabel: {
          display: true,
          labelString: "Percentage through Add/Drop Period",
        },
      },
    ],
    yAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
          min: 0,
          max: 1,
        },
      },
    ],
  },
};

const percentSectionChartOptions = {
  elements: {
    point: {
      radius: 0,
    },
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start",
  },
  scales: {
    autoSkip: true,
    xAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          beginAtZero: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
          max: 100,
          stepSize: 10,
          callback: function(value) {
            return value + "%";
          },
        },

        scaleLabel: {
          display: true,
          labelString: "Percentage through Add/Drop Period",
        },
      },
    ],
    yAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
          min: 0,
          max: 100,
          callback: function(value) {
            return value + "%";
          },
        },
      },
    ],
  },
};

const translateSemester = (semester) => {
  const year = semester.substring(0, 4);
  const season = semester.substring(4);
  if (season === "A") {
    return "Spring " + year;
  } else if (season === "B") {
    return "Summer " + year;
  } else if (season === "C") {
    return "Fall " + year;
  }
  return year;
};

const GraphBox = ({ courseCode, courseData, isAverage }) => {
  const [loaded, setLoaded] = useState(false);
  const [pcaDemandChartData, setPCADemandChartData] = useState();
  const [percentSectionsChartData, setPercentSectionsChartData] = useState();
  const [semester, setSemester] = useState();

  useEffect(() => {
    if (!courseCode) {
      return;
    }

    setLoaded(false);

    const averageOrRecent = isAverage ? "average_reviews" : "recent_reviews";

    setSemester(courseData[averageOrRecent]["rSemesterCalc"]);

    const pcaDemandPlot = courseData[averageOrRecent]["pca_demand_plot"];
    if (pcaDemandPlot) {
      setPCADemandChartData(generateChartData(pcaDemandPlot, false));
    }

    const percentSectionsPlot =
      courseData[averageOrRecent]["percent_open_plot"];
    if (percentSectionsPlot) {
      setPercentSectionsChartData(generateChartData(percentSectionsPlot, true));
    }

    setLoaded(true);
  }, [courseCode]);

  console.log(courseData);
  return (
    <>
      {/* <div id="content" className="row"> */}
      <div className="col-sm-12 box-wrapper" style={{ width: "50%" }}>
        <div className="box">
          {pcaDemandChartData ? (
            <div id="row-select-chart-container">
              <ChartTitle>
                Historically, how difficult has it been to get into {courseCode}{" "}
                during the add/drop period?
              </ChartTitle>
              <ChartDescription>
                'Difficulty' is represented on a 0-1 scale (relative to all
                classes at Penn), plotted over time as a % of add/drop period
                elapsed, using Penn Course Alert data from semesters since
                {translateSemester(semester)})
              </ChartDescription>
              <Bar data={pcaDemandChartData} options={chartOptions} />
            </div>
          ) : (
            <div>
              {" "}
              {loaded ? (
                "No demand plot for this course"
              ) : (
                <LoadingContainer>
                  <i
                    className="fa fa-spin fa-cog fa-fw"
                    style={{ fontSize: "150px", color: "#aaa" }}
                  />
                  <h1 style={{ fontSize: "2em", marginTop: 15 }}>Loading...</h1>
                </LoadingContainer>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="col-sm-12 box-wrapper" style={{ width: "50%" }}>
        <div className="box">
          {percentSectionsChartData ? (
            <div id="row-select-chart-container">
              <ChartTitle>
                Percent of sections open for {courseCode} during the add/drop
                period
              </ChartTitle>
              <ChartDescription>
                Based on Penn inTouch registration data since{" "}
                {translateSemester(semester)}. Calculated by number of sections
                open divided by the total number of sections.
              </ChartDescription>
              <Bar
                data={percentSectionsChartData}
                options={percentSectionChartOptions}
              />
            </div>
          ) : (
            <div>
              {" "}
              {loaded ? (
                "No demand plot for this course"
              ) : (
                <LoadingContainer>
                  <i
                    className="fa fa-spin fa-cog fa-fw"
                    style={{ fontSize: "150px", color: "#aaa" }}
                  />
                  <h1 style={{ fontSize: "2em", marginTop: 15 }}>Loading...</h1>
                </LoadingContainer>
              )}
            </div>
          )}
        </div>
      </div>
      {/* </div> */}
    </>
  );
};

export default GraphBox;
