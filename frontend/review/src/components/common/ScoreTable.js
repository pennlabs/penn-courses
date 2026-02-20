import React, { useEffect, useState } from "react";
import { PERCENTAGE_COLUMNS } from "../../constants/values";
import ReactTable from "react-table";
import ReactTooltip from "react-tooltip";

export const ScoreTable = props => {
  const {
    columns,
    alternating = false,
    noun,
    multi,
    data = [],
    onSelect = () => {},
    ignoreSelect = false,
    isAverage = null,
    isCourseEval = null
  } = props;
  const [selected, setSelected] = useState(multi ? {} : null);
  const [sorted, setSorted] = useState(props.sorted);

  // Force rerender of table content when isAverage changes
  // TODO: Move isAverage into localstorage or redux store
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setSorted([...sorted]), [isAverage, isCourseEval]);
  useEffect(() => {
    const selected = multi ? {} : null;
    setSelected(selected);
    onSelect && onSelect(selected);
  }, [data, multi, onSelect]);

  const getTrProps = (_, rowInfo) => {
    const { index, original, row } = rowInfo;
    const noRow = multi ? index in selected : index === selected;
    return rowInfo && row
      ? {
          style: alternating
            ? {
                backgroundColor: row._viewIndex % 2 ? "#F5F8F8" : "white"
              }
            : {},
          onClick: () => {
            if (ignoreSelect) {
              return;
            }
            // Recalculate value every time onClick is called
            const noRow = multi ? index in selected : index === selected;
            if (!multi) {
              const { key } = original;
              onSelect(noRow ? null : key);
              setSelected(noRow ? null : index);
              return;
            }
            if (noRow) {
              delete selected[index];
            } else {
              selected[index] = rowInfo;
            }
            onSelect(selected);
            setSelected({ ...selected });
          },
          className: ignoreSelect ? "ignore-select" : noRow ? "selected" : ""
        }
      : {};
  };

  // Convert relevant columns to percentages
  data.forEach(row => {
    PERCENTAGE_COLUMNS.forEach(title => {
      if (row[title] && row[title].average) {
        row[title].average =
          row[title].average.slice(-1) === "%"
            ? row[title].average
            : `${Math.floor(parseFloat(row[title].average) * 100)}%`;
      }
      if (row[title] && row[title].recent) {
        row[title].recent =
          row[title].recent.slice(-1) === "%"
            ? row[title].recent
            : `${Math.floor(parseFloat(row[title].recent) * 100)}%`;
      }
      if (!isNaN(row[title])) {
        row[title] = `${Math.floor(parseFloat(row[title]) * 100)}%`;
      }
    });
  });

  columns.forEach(col => {
    if (col.Header === "Final Enrollment") {
      col.Header = (
        <>
          Final Enrollment{" "}
          <span data-tip data-for="final-enrollment">
            <i
              className="fa fa-question-circle"
              style={{ color: "#c6c6c6", fontSize: "13px" }}
            />
          </span>
          <ReactTooltip
            id="final-enrollment"
            className="opaque"
            type="light"
            effect="solid"
            border={true}
            borderColor="#ededed"
            textColor="#4a4a4a"
          >
            <span className="tooltip-text">The average final enrollment.</span>
          </ReactTooltip>
        </>
      );
    } else if (col.Header === "Num Openings") {
      col.Header = (
        <>
          Num Openings{" "}
          <a data-tip data-for="num-openings">
            <i
              className="fa fa-question-circle"
              style={{ color: "#c6c6c6", fontSize: "13px" }}
            />
          </a>
          <ReactTooltip
            id="num-openings"
            className="opaque"
            type="light"
            effect="solid"
            border={true}
            borderColor="#ededed"
            textColor="#4a4a4a"
          >
            <span className="tooltip-text">
              Averaged across all sections,
              <br />
              the number of times the section changed from
              <br />
              closed to open during the add/drop period.
            </span>
          </ReactTooltip>
        </>
      );
    } else if (col.Header === "Percent Open") {
      col.Header = (
        <>
          Percent Open{" "}
          <a data-tip data-for="percent-open">
            <i
              className="fa fa-question-circle"
              style={{ color: "#c6c6c6", fontSize: "13px" }}
            />
          </a>
          <ReactTooltip
            id="percent-open"
            className="opaque"
            type="light"
            effect="solid"
            border={true}
            borderColor="#ededed"
            textColor="#4a4a4a"
          >
            <span className="tooltip-text">
              Averaged across all sections,
              <br />
              the percentage of time during the add/drop period
              <br />
              that the section was open for registration.
            </span>
          </ReactTooltip>
        </>
      );
    } else if (col.Header === "Filled In Adv Reg") {
      col.Header = (
        <>
          Filled in Adv Reg{" "}
          <a data-tip data-for="filled-in-adv-reg">
            <i
              className="fa fa-question-circle"
              style={{ color: "#c6c6c6", fontSize: "13px" }}
            />
          </a>
          <ReactTooltip
            id="filled-in-adv-reg"
            className="opaque"
            type="light"
            effect="solid"
            border={true}
            borderColor="#ededed"
            textColor="#4a4a4a"
          >
            <span className="tooltip-text">
              The percentage of sections that were
              <br />
              fully filled during advance registration.
            </span>
          </ReactTooltip>
        </>
      );
    }
  });
  return (
    <div>
      <ReactTable
        className="mb-2"
        {...props}
        showPagination={false}
        resizable={true}
        style={{ maxHeight: 400 }}
        getTrProps={getTrProps}
        minRows={0}
        pageSize={data.length}
        sorted={sorted}
        onSortedChange={setSorted}
      />
      <span id="course-table_info">
        Showing {data.length} {(noun || "row") + (data.length !== 1 ? "s" : "")}
      </span>
    </div>
  );
};
