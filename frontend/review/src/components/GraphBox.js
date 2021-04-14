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
  font-size: 20px;
  font-weight: bold;
  text-align: center;
`;

const ChartDescription = styled.div`
  font-size: 14px;
  font-weight: normal;
  color: #b2b2b2;
  text-align: center;
`;

const sumOfSubArray = (start, end, data) => {
  let sum = 0;
  for (let i = start; i <= end; i++) {
    sum += data[i][1];
  }
  return sum;
};

const generateChartData = (data) => {
  return {
    labels: data.map((point) => Math.round(point[0] * 100)),
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
          return Math.round(average * 100) / 100;
        }),
        borderColor: "#1866D2",
        borderWidth: 3,
        fill: false,
      },
      {
        type: "bar",
        label: "Demand",
        data: data.map((point) => Math.round(point[1] * 100) / 100),
        backgroundColor: "#AECBFA",
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

const GraphBox = ({ courseCode, courseData }) => {
  const [loaded, setLoaded] = useState(false);
  const [pcaDemandChartData, setPCADemandChartData] = useState();
  const [percentSectionsChartData, setPercentSectionsChartData] = useState();
  const [semester, setSemester] = useState();

  useEffect(() => {
    if (!courseCode) {
      return;
    }

    setLoaded(false);
    setSemester(courseData["recent_reviews"]["rSemesterCalc"]);

    const pcaDemandPlot = courseData["recent_reviews"]["pca_demand_plot"];
    if (pcaDemandPlot) {
      setPCADemandChartData(generateChartData(pcaDemandPlot));
    }

    const percentSectionsPlot =
      courseData["recent_reviews"]["percent_open_plot"];
    if (percentSectionsPlot) {
      setPercentSectionsChartData(generateChartData(percentSectionsPlot));
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
                Historical PCA Demand For {courseCode} During Add/Drop
              </ChartTitle>
              <ChartDescription>
                Based on Penn Course Alert registration averages since{" "}
                {translateSemester(semester)} and section capacity data.
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
                Percent of Sections Open For {courseCode} During Add/Drop
              </ChartTitle>
              <ChartDescription>
                Based on PennInTouch registration data since{" "}
                {translateSemester(semester)}. Calculated by number of sections
                open divided by the total number of sections.
              </ChartDescription>
              <Bar data={percentSectionsChartData} options={chartOptions} />
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
